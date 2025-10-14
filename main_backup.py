from strands.models import BedrockModel
from strands.tools.mcp import MCPClient
from strands import Agent

from mcp import StdioServerParameters, stdio_client
import logging
import os
from datetime import datetime
import re
import shutil

logging.getLogger("strands").setLevel(logging.INFO)

logging.basicConfig(
    format="%(levelname)s | %(name)s | %(message)s", handlers=[logging.StreamHandler()]
)

bedrock_model = BedrockModel(
    model_id="apac.anthropic.claude-sonnet-4-20250514-v1:0",
    region_name="ap-southeast-2",
)

aws_diag_client = MCPClient(
    lambda: stdio_client(
        StdioServerParameters(
            command="uvx", args=["awslabs.aws-diagram-mcp-server@latest"]
        )
    )
)


def extract_diagram_path(agent_result):
    """Extract diagram path from agent result."""
    result_str = str(agent_result)

    # Look for explicit diagram path
    for line in result_str.split("\n"):
        if "The diagram is saved at:" in line:
            return line.split("The diagram is saved at:")[1].strip()

    # Fallback: search for diagram file patterns
    diagram_pattern = r"([^\s]+\.(?:png|jpg|jpeg|svg|pdf))"
    matches = re.findall(diagram_pattern, result_str, re.IGNORECASE)
    return matches[0] if matches else None


def handle_diagram_file(original_path, target_dir):
    """Handle diagram file movement and return local path."""
    if not original_path:
        return None

    filename = os.path.basename(original_path)
    local_path = os.path.join(target_dir, filename)

    # If file already exists locally, use it
    if os.path.exists(local_path):
        print(f" Diagram already exists at: {local_path}")
        return local_path

    # Try to copy from original location
    if os.path.exists(original_path):
        try:
            shutil.copy2(original_path, local_path)
            print(f" Moved diagram from {original_path} to {local_path}")
            return local_path
        except Exception as e:
            print(f" Warning: Could not move diagram file: {e}")
            return original_path

    print(f" Warning: Diagram file not found at {original_path}")
    return None


def create_markdown_content(query, agent_result, diagram_path):
    """Create markdown content with optional diagram reference."""
    content = f"""# AWS CloudWAN Architecture Design

**Generated on:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

**Query:** {query}

## Architecture Diagram
"""

    if diagram_path:
        filename = os.path.basename(diagram_path)
        content += f"![AWS CloudWAN Architecture]({filename})\n\n"
        content += f"**Diagram Location:** `{diagram_path}`\n\n"
    else:
        content += "*Diagram generation failed or file not found*\n\n"

    content += f"""## Design Details and Implementation Guide

{agent_result}

---

## Next Steps

1. Review the architecture design above
2. Validate the design meets your specific requirements
3. Use the implementation guide to deploy the infrastructure
4. Test connectivity and security controls
5. Monitor performance and costs
"""

    return content


SYSTEM_PROMPT = """
You are an expert AWS Solutions Architect with deep knowledge of the AWS Well-Architected Framework.

Your primary role is to design robust, secure, and scalable AWS Landing Zones for new and existing cloud environments.

When a user requests a landing zone design, your process is as follows:

Requirement Gathering: Ask clarifying questions to understand the user's specific business needs,
compliance requirements (e.g., HIPAA, PCI DSS), technical constraints, and desired account structure.

Well-Architected Design: Based on the gathered information, design a landing zone architecture that
strictly adheres to the five pillars of the Well-Architected Framework: Operational Excellence, Security, Reliability, Performance Efficiency, and Cost Optimization.

Every design decision you make must be justified by one or more of these pillars.

Output Generation: Provide the design in a three-part output:

Textual Design: A detailed, step-by-step description of the architecture. This must cover account organization (AWS Organizations), networking (VPCs, Transit Gateway), 
security controls (Control Tower, SCPs), identity management (IAM), and logging/monitoring (CloudTrail, CloudWatch).

Diagrams: Generate a clear, professional diagram to visually represent the architecture.
The diagram should show the flow of resources, account relationships, and key services. Describe the layout using a format that can be easily understood and replicated.

Backlog: Create a backlog of stories to implement the design, with t-shirt sizing Large, Medium, Small, description and definition of done.
Split into 2-week sprints for implementation.

Tone & Interaction: Maintain a professional, knowledgeable, and helpful tone. Always explain the
rationale behind your design choices, explicitly referencing the relevant Well-Architected pillars.

You are a consultant, not just a generator. You will continue to iterate on the design based on user feedback.

Always provide clear, actionable advice with to create this infrastructure from digram. Default region is ap-southeast-2.

You MUST tell the customer the full file path of the diagram in the format "The diagram is saved at: <filepath>".

When generating diagrams, save them to the ./outputs directory with descriptive filenames.
"""

# Set up diagram output directory

diagram_dir = "./outputs"

os.makedirs(diagram_dir, exist_ok=True)

with aws_diag_client:
    all_tools = aws_diag_client.list_tools_sync()

    agent = Agent(tools=all_tools, model=bedrock_model, system_prompt=SYSTEM_PROMPT)

    query = (
        "Design a real-world AWS cloudWAN network across Melbourne and Sydney "
        "regions that must have centralised packet inspection, decentralised egress, centralied ingress"
        "that will host web applications which serves thousands of users with low latency, strong security controls, and predictable costs."
    )

    print(f"Sending query to agent: {query}\n")

    agent_result = agent(query)

    # Process diagram and create documentation
    original_diagram_path = extract_diagram_path(agent_result)
    local_diagram_path = handle_diagram_file(original_diagram_path, diagram_dir)

    # Generate markdown documentation
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    markdown_filename = f"aws_design_{timestamp}.md"
    markdown_path = os.path.join(diagram_dir, markdown_filename)

    markdown_content = create_markdown_content(query, agent_result, local_diagram_path)
    markdown_content += f"\n**Documentation saved at:** `{markdown_path}`\n"

    # Save markdown file
    try:
        with open(markdown_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        print(f"\n{'=' * 60}")
        print(f"Design documentation saved successfully!")
        print(f"Markdown file: {markdown_path}")
        if local_diagram_path:
            print(f" Diagram file: {local_diagram_path}")
        print(f"{'=' * 60}")

    except Exception as e:
        print(f"\n Error saving markdown file: {e}")
        print(f"Agent result: {agent_result}")


def main():
    print("AWS landing zone designer")


if __name__ == "__main__":
    main()
