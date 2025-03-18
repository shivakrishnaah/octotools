import os
import base64
import xml.etree.ElementTree as ET
from octotools.tools.base import BaseTool
from octotools.engine.openai import ChatOpenAI
from datetime import datetime

class Mxgraph_Generator_Tool(BaseTool):
    require_llm_engine = True

    def __init__(self, model_string="gpt-4o-mini"):
        super().__init__(
            tool_name="Mxgraph_Generator_Tool",
            tool_description="A tool that converts a text description of an AWS architecture into a pure, valid mxGraph XML format for Diagrams.net (Draw.io), incorporating AWS service icons, foundational components (e.g., VPC, gateways), and container services where applicable.",
            tool_version="1.0.3",
            input_types={
                "prompt": "str - A text description of the AWS architecture to convert into a diagram (e.g., 'A cloud architecture with AWS Lambda, Amazon S3, and Amazon RDS')."
            },
            output_type="str - The generated mxGraph XML string with AWS service icons.",
            demo_commands=[
                {
                    "command": 'execution = tool.execute(prompt="A cloud architecture with AWS Lambda, Amazon S3, and Amazon RDS")',
                    "description": "Generate an mxGraph XML diagram with AWS4 icons, including foundational components like VPC."
                },
                {
                    "command": 'execution = tool.execute(prompt="A containerized microservices system with Amazon ECS and Amazon DynamoDB")',
                    "description": "Generate an mxGraph XML diagram with container services and foundational components with AWS4 icons"
                }
            ],
            user_metadata={
                "limitation": ( 
                     "The tool relies on ChatGPT to map services to correct resIcon values and colors, which may occasionally be inaccurate. "
                     "Layout may require manual adjustment in Diagrams.net. "
                     "Note: This tool can be added only once in the prompt pipeline."
                     ),
                "best_practice": (
                    "1) Use AWS-specific service names (e.g., 'AWS Lambda', 'Amazon S3').\n"
                    "2) Specify relationships (e.g., 'connected to', 'with') for accurate connections.\n"
                    "3) Verify the XML in Diagrams.net to ensure correct icon mapping and refine layout as needed."
                )
            }
        )
        self.model_string = model_string

    def execute(self, prompt):
        print(f"\nInitializing TextToMxGraphDiagramTool with model: {self.model_string}")
        llm_engine = ChatOpenAI(model_string=self.model_string, is_multimodal=False)

        system_prompt = (
            "You are an expert in generating AWS architecture diagrams in mxGraph XML format for Diagrams.net (Draw.io). Given a text description of an AWS architecture, produce a pure, valid mxGraph XML string that represents the diagram, with no additional text or output beyond the XML itself. Every node must use the built-in Diagrams.net AWS4 shape library with 'shape=mxgraph.aws4.resourceIcon' and the correct 'resIcon' value, without exception—do not use generic shapes like 'rounded=1', 'shape=rectangle', or 'shape=ellipse'. Follow these rules to ensure the XML is error-free and produces a comprehensive diagram:\n"
            "1. For each AWS service, map it to the exact 'resIcon' value from the Diagrams.net AWS4 library. Examples include:\n"
            "   - 'mxgraph.aws4.lambda' for AWS Lambda\n"
            "   - 'mxgraph.aws4.simple_storage_service' for Amazon S3\n"
            "   - 'mxgraph.aws4.rds' for Amazon RDS\n"
            "   - 'mxgraph.aws4.emr' for Amazon EMR\n"
            "   - 'mxgraph.aws4.sagemaker' for Amazon SageMaker\n"
            "   - 'mxgraph.aws4.step_functions' for AWS Step Functions\n"
            "   - 'mxgraph.aws4.glue' for AWS Glue\n"
            "   - 'mxgraph.aws4.dms' for AWS Database Migration Service (DMS)\n"
            "   - 'mxgraph.aws4.dynamodb' for Amazon DynamoDB\n"
            "   - 'mxgraph.aws4.managed_workflows_for_apache_airflow' for Amazon MWAA\n"
            "   - 'mxgraph.aws4.virtual_private_cloud' for Amazon VPC\n"
            "   - 'mxgraph.aws4.storage_gateway' for AWS Storage Gateway\n"
            "2. For non-AWS components (e.g., 'Data Source', 'Model Development'), use 'resIcon=mxgraph.aws4.general' as a fallback.\n"
            "3. For combined services (e.g., 'AWS Glue / DMS'), choose the primary service’s 'resIcon' (e.g., 'mxgraph.aws4.glue') or split into separate nodes if contextually appropriate.\n"
            "4. Use the style 'shape=mxgraph.aws4.resourceIcon;resIcon=<service-icon>;sketch=0;fillColor=#<service-color>;strokeColor=#ffffff;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=12;fontStyle=0;aspect=fixed', where <service-color> is the official AWS category color (e.g., #FF9900 for Compute, #7AA116 for Storage, #CC2264 for Database, #00A1C9 for Analytics, #CC2264 for Machine Learning, #007DBC for Networking).\n"
            "5. Set node size to width=78, height=78, with precise coordinates (x, y) for layout.\n"
            "6. Include edges (arrows) for connections between services using valid 'source' and 'target' IDs. Infer connections from the description or logical flow if not explicitly stated (e.g., sequential components imply connections).\n"
            "7. Enhance the diagram with foundational AWS components like Amazon VPC (resIcon=mxgraph.aws4.virtual_private_cloud) where appropriate, even if not mentioned, to reflect a realistic architecture. and use few services diagrams as containers to hold other services (Example: VPC container or EKS containers to hold other services)\n"
            "8. Ensure the XML adheres strictly to mxGraph structure: start with '<mxGraphModel><root>', include a parent cell (id='0'), a layer cell (id='1' parent='0'), and properly formatted child cells for nodes and edges, ending with '</root></mxGraphModel>'.\n"
            "9. Do not include any invalid syntax, missing tags, generic shapes, or extraneous content outside the XML. Every node must use 'shape=mxgraph.aws4.resourceIcon' with a valid 'resIcon'.\n"
            "Example:\n"
            "Text: 'Data Source connected to AWS Glue / DMS, then to Amazon S3 and Amazon SageMaker'\n"
            "Output:\n"
            "<mxGraphModel><root><mxCell id=\"0\"/><mxCell id=\"1\" parent=\"0\"/><mxCell id=\"2\" value=\"Amazon VPC\" style=\"shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.virtual_private_cloud;sketch=0;fillColor=#007DBC;strokeColor=#ffffff;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=12;fontStyle=0;aspect=fixed\" vertex=\"1\" parent=\"1\"><mxGeometry x=\"20\" y=\"20\" width=\"78\" height=\"78\" as=\"geometry\"/></mxCell><mxCell id=\"3\" value=\"Data Source\" style=\"shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.general;sketch=0;fillColor=#D86613;strokeColor=#ffffff;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=12;fontStyle=0;aspect=fixed\" vertex=\"1\" parent=\"1\"><mxGeometry x=\"120\" y=\"20\" width=\"78\" height=\"78\" as=\"geometry\"/></mxCell><mxCell id=\"4\" value=\"AWS Glue / DMS\" style=\"shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.glue;sketch=0;fillColor=#00A1C9;strokeColor=#ffffff;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=12;fontStyle=0;aspect=fixed\" vertex=\"1\" parent=\"1\"><mxGeometry x=\"220\" y=\"20\" width=\"78\" height=\"78\" as=\"geometry\"/></mxCell><mxCell id=\"5\" value=\"Amazon S3\" style=\"shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.simple_storage_service;sketch=0;fillColor=#7AA116;strokeColor=#ffffff;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=12;fontStyle=0;aspect=fixed\" vertex=\"1\" parent=\"1\"><mxGeometry x=\"320\" y=\"20\" width=\"78\" height=\"78\" as=\"geometry\"/></mxCell><mxCell id=\"6\" value=\"Amazon SageMaker\" style=\"shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.sagemaker;sketch=0;fillColor=#CC2264;strokeColor=#ffffff;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=12;fontStyle=0;aspect=fixed\" vertex=\"1\" parent=\"1\"><mxGeometry x=\"420\" y=\"20\" width=\"78\" height=\"78\" as=\"geometry\"/></mxCell><mxCell id=\"7\" edge=\"1\" source=\"2\" target=\"3\" parent=\"1\"><mxGeometry relative=\"1\" as=\"geometry\"/></mxCell><mxCell id=\"8\" edge=\"1\" source=\"3\" target=\"4\" parent=\"1\"><mxGeometry relative=\"1\" as=\"geometry\"/></mxCell><mxCell id=\"9\" edge=\"1\" source=\"4\" target=\"5\" parent=\"1\"><mxGeometry relative=\"1\" as=\"geometry\"/></mxCell><mxCell id=\"10\" edge=\"1\" source=\"4\" target=\"6\" parent=\"1\"><mxGeometry relative=\"1\" as=\"geometry\"/></mxCell></root></mxGraphModel>\n\n"
            "Now, generate a pure mxGraph XML string for the following AWS architecture description."
            )

        try:
            full_prompt = f"{system_prompt}\n\nArchitecture description: {prompt}"
            response = llm_engine(full_prompt)
            return response.strip()
        except Exception as e:
            return f"Error generating mxGraph XML: {str(e)}"

    def get_metadata(self):
        metadata = super().get_metadata()
        return metadata

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"Script directory: {script_dir}")

    tool = Mxgraph_Generator_Tool(model_string="gpt-4o-mini")
    metadata = tool.get_metadata()
    print(metadata)

    prompt = "A cloud architecture with AWS Lambda, Amazon S3, and Amazon RDS"
    try:
        execution = tool.execute(prompt=prompt)
        print("Generated mxGraph XML:")
        print(execution)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(script_dir, f"diagram_{timestamp}.xml")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(execution)
        print(f"XML written to: {output_file}")
    except Exception as e:
        print(f"Execution failed: {e}")

    print("Done!")