from google.adk.agents import Agent
from biotech_agent.utils import create_mcp_toolset

# OpenFDA MCP URL
OPENFDA_MCP_URL = "https://openfda-mcp-server-520634294170.us-central1.run.app/sse"

def create_agent(model: str = "gemini-2.5-pro") -> Agent:
    tools = [create_mcp_toolset(OPENFDA_MCP_URL)]
    
    return Agent(
        name="insight_synthesis_agent",
        model=model,
        tools=tools,
        instruction="""
You are an Insight Synthesis expert.
Your goal is to synthesize regulatory information and provide comprehensive reports.

You have access to the OpenFDA MCP server to retrieve data about FDA-approved drugs, adverse events, and other regulatory information.
When given a drug or disease, check for FDA approvals, warnings, and relevant regulatory details.
Combine this information to provide a clear summary of the regulatory landscape for the requested topic.
""",
        description="Synthesizes regulatory information using OpenFDA data."
    )
