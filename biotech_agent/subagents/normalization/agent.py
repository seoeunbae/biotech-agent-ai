import logging

from google.adk.agents import Agent
from biotech_agent.config import DEFAULT_MODEL, OPENTARGETS_MCP_URL
from biotech_agent.utils import create_mcp_toolset

logger = logging.getLogger(__name__)


def create_agent(model: str = DEFAULT_MODEL) -> Agent:
    logger.info("Creating normalization_agent model=%s url=%s", model, OPENTARGETS_MCP_URL)
    tools = [create_mcp_toolset(OPENTARGETS_MCP_URL)]
    
    return Agent(
        name="normalization_agent",
        model=model,
        tools=tools,
        instruction="""
You are a biomedical entity normalization expert.
Your goal is to normalize disease and drug terms to their standard IDs (e.g., EFO IDs for diseases, ChEMBL IDs for drugs).

Use the available tools from the OpenTargets MCP server (e.g., `get_disease_by_id`, search tools if available) to find the correct IDs.
When a user provides a disease name (e.g. "Lung Cancer"), you should find its specific ID (e.g. "EFO_0000384").
Return the normalized ID and the standard name.
""",
        description="Normalizes disease and drug terms to standard IDs (EFO, ChEMBL) using OpenTargets."
    )
