import streamlit as st
import subprocess
import json
import os
import re
from PIL import Image

# Set up Streamlit UI
st.title("Architecture Diagram Generator")
st.write("Upload an image of a system architecture and enter a query to generate an updated AWS architecture diagram.")

# Sidebar for tool selection
st.sidebar.header("Select Enabled Tools")

TOOL_OPTIONS = {
    "Relevant_Patch_Zoomer_Tool": "Identify and zoom into relevant areas",
    "Python_Code_Generator_Tool": "Generate Python code for automation",
    "Image_Captioner_Tool": "Generate textual descriptions of uploaded images",
    "AWS_Diagram_Generator_Tool": "Generate AWS architecture diagram using Diagrams library"
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

        # Check for AWS diagram output
        aws_diagram_pattern = re.compile(r'==>Executed Result:\s*\[\s*{\s*"image":\s*"([^"]+)"\s*}\s*\]')
        aws_diagram_match = aws_diagram_pattern.search(text)
        
        if aws_diagram_match:
            aws_diagram_path = aws_diagram_match.group(1)
            if os.path.exists(aws_diagram_path):
                st.subheader("Generated AWS Architecture Diagram")
                try:
                    # Display the AWS diagram
                    aws_image = Image.open(aws_diagram_path)
                    st.image(aws_image, caption="AWS Architecture Diagram", use_column_width=True)
                except Exception as e:
                    st.error(f"Error displaying AWS diagram: {str(e)}")
            else:
                st.error(f"AWS diagram file not found at: {aws_diagram_path}")
        else:
            st.info("No AWS diagram was generated. Make sure AWS_Diagram_Generator_Tool is selected in the sidebar.")