import streamlit as st
import subprocess
import json
import os
import re

# Set up Streamlit UI
st.title("Architecture Diagram Generator")
st.write("Upload an image of a system architecture and enter a query to generate an updated AWS architecture diagram.")

# Sidebar for tool selection
st.sidebar.header("Select Enabled Tools")

TOOL_OPTIONS = {
    "Mxgraph_Generator_Tool": "Convert components into an AWS architecture diagram",
    "Relevant_Patch_Zoomer_Tool": "Identify and zoom into relevant areas",
    "Python_Code_Generator_Tool": "Generate Python code for automation",
    "Image_Captioner_Tool": "Generate textual descriptions of uploaded images"
}

selected_tools = [
    tool for tool, desc in TOOL_OPTIONS.items() if st.sidebar.checkbox(desc, value=True)
]

# Inputs
query = st.text_area("Enter your query:")
image_file = st.file_uploader("Upload architecture image", type=["png", "jpg", "jpeg"])

if st.button("Generate Diagram"):
    if not query or not image_file:
        st.error("Please provide both a query and an image.")
    else:
        # Save image temporarily
        image_path = f"images/{image_file.name}"
        os.makedirs("images", exist_ok=True)
        with open(image_path, "wb") as f:
            f.write(image_file.read())

        # Create data input for solve.py
        data = [{
            "pid": "2",
            "question": query,
            "image": image_path,
            "query": query,
            "answer": "",
        }]
        data_file = "input_data.json"
        with open(data_file, "w") as f:
            json.dump(data, f)

        # Define parameters
        LLM = "gpt-4o"
        INDEX = 0
        CACHE_DIR = "cache"
        OUT_DIR = "output"
        os.makedirs(CACHE_DIR, exist_ok=True)
        os.makedirs(OUT_DIR, exist_ok=True)

        # Join selected tools into a comma-separated string
        ENABLED_TOOLS = ",".join(selected_tools)

        # Run solve.py and capture output
        command = [
            "python", "solve.py",
            "--index", str(INDEX),
            "--task", query,
            "--data_file", data_file,
            "--llm_engine_name", LLM,
            "--root_cache_dir", CACHE_DIR,
            "--output_json_dir", OUT_DIR,
            "--output_types", "direct",
            "--enabled_tools", ENABLED_TOOLS,
            "--max_time", "300"
        ]

        st.write("Processing... Please wait.")
        output_placeholder = st.empty()
        error_placeholder = st.empty()

        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        # Collect logs
        output_logs = []
        error_logs = []
        text = ""
        for line in iter(process.stdout.readline, ''):
            output_logs.append(line.strip())
            text = "\n".join(output_logs)
            output_placeholder.text_area("Logs:", text, height=300)

        for line in iter(process.stderr.readline, ''):
            error_logs.append(line.strip())
            error_placeholder.text_area("Errors:", "\n".join(error_logs), height=300, help="Check these errors for debugging.")

        process.wait()
        xml_output = ""
        xml_pattern = re.compile(r"```xml\n(.*?)\n```", re.DOTALL)
        match = xml_pattern.search(text)
        if match:
                xml_output = match.group(1)

        if xml_output:
            st.subheader("Generated mxGraph XML:")
            st.code(xml_output, language="xml")

                    # Embed the mxGraph XML inside an interactive viewer
            html_code = f"""
                    <iframe
                        src="https://www.draw.io/?embed=1&ui=atlas&spin=1&proto=json&saveAndExit=0&noSaveBtn=1&noExitBtn=1&noOpen=1&noSave=1#R{xml_output}"
                        width="100%"
                        height="600px"
                        frameborder="0"
                    ></iframe>
                    """
            st.subheader("Interactive mxGraph Diagram")
            st.components.v1.html(html_code, height=650)

        else:
            st.error("No valid mxGraph XML found in output.json.")