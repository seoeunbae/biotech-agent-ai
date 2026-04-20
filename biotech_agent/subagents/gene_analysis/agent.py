import logging

from google.adk.agents import Agent
from biotech_agent.config import DEFAULT_MODEL, GENE_ONTOLOGY_MCP_URL, OPENGENES_MCP_URL
from biotech_agent.utils import create_mcp_toolset

logger = logging.getLogger(__name__)


def create_agent(model: str = DEFAULT_MODEL) -> Agent:
    logger.info("Creating gene_analysis_agent model=%s", model)
    tools = [
        create_mcp_toolset(OPENGENES_MCP_URL),
        create_mcp_toolset(GENE_ONTOLOGY_MCP_URL)
    ]
    
    return Agent(
        name="gene_analysis_agent",
        model=model,
        tools=tools,
        instruction="""
You are a Gene Analysis expert.
Your goal is to analyze gene-disease associations and understand biological mechanisms.

You have access to:
1. OpenGenes MCP: Contains longevity and aging related gene data. Use this to find genes associated with specific conditions or interventions.
2. Gene Ontology MCP: Use this to search for GO terms and understand the biological functions of genes.

When given a disease ID or name, find associated genes.
When given a gene, analyze its function.
Merge information from both sources to provide a comprehensive analysis.
""",
        description="Analyzes gene-disease associations and biological mechanisms using OpenGenes and Gene Ontology."
    )
