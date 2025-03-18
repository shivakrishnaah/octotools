import os
import json
import time
from typing import List
import uuid
import shutil
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from octotools.models.initializer import Initializer
from octotools.models.planner import Planner
from octotools.models.memory import Memory
from octotools.models.executor import Executor
from octotools.models.utlis import make_json_serializable_truncated

app = FastAPI()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)  # Ensure the upload directory exists

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins (Frontend can make requests)
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)
@app.post("/upload")
async def upload_image(image: UploadFile = File(...)):
    ext = os.path.splitext(image.filename)[-1].lower()
    random_filename = f"{uuid.uuid4().hex}{ext}"  # Generate a unique filename
    image_path = os.path.join(UPLOAD_DIR, random_filename)

    with open(image_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)  # Save the file

    return {"filename": random_filename}

class SolveRequest(BaseModel):
    query: str
    image: str
    enabledTools: List[str]
    llm: str = "gpt-4o"

@app.post("/solve")
async def solve(request: SolveRequest):
    query = request.query
    image_filename = request.image
    image_path = os.path.join(UPLOAD_DIR, image_filename)

    if not os.path.exists(image_path):
        raise HTTPException(status_code=400, detail=f"Image '{image_filename}' not found.")

    # Initialize components
    enabled_tools = request.enabledTools
    llm = request.llm
    initializer = Initializer(enabled_tools=enabled_tools, model_string=llm)
    planner = Planner(llm_engine_name=llm,
                      toolbox_metadata=initializer.toolbox_metadata,
                      available_tools=initializer.available_tools)
    memory = Memory()
    executor = Executor(llm_engine_name=llm)

    async def event_generator():
        start_time = time.time()
        step_count = 0

        yield json.dumps({"step": "received", "query": query, "image": image_filename}) + "\n"

        base_response = planner.generate_base_response(query, image_path)
        yield json.dumps({"step": "base_response", "data": base_response}) + "\n"

        query_analysis = planner.analyze_query(query, image_path)
        yield json.dumps({"step": "query_analysis", "data": query_analysis}) + "\n"

        while step_count < 10 and (time.time() - start_time) < 60:
            step_count += 1
            next_step = planner.generate_next_step(query, image_path, query_analysis, memory, step_count, 10)
            context, sub_goal, tool_name = planner.extract_context_subgoal_and_tool(next_step)

            if tool_name not in planner.available_tools:
                yield json.dumps({"step": step_count, "error": f"Tool '{tool_name}' not found."}) + "\n"
                break

            tool_command = executor.generate_tool_command(query, image_path, context, sub_goal, tool_name, planner.toolbox_metadata[tool_name])
            explanation, command = executor.extract_explanation_and_command(tool_command)
            result = executor.execute_tool_command(tool_name, command)
            result = make_json_serializable_truncated(result)

            memory.add_action(step_count, tool_name, sub_goal, command, result)
            yield json.dumps({"step": step_count, "command": command, "result": result}) + "\n"

        final_output = planner.generate_final_output(query, image_path, memory)
        yield json.dumps({"step": "final_output", "data": final_output}) + "\n"

    return StreamingResponse(event_generator(), media_type="application/json")