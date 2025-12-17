from google.adk.agents import Agent
from biotech_agent.utils import create_mcp_toolset

# MCP URLs
OPENGENES_MCP_URL = "https://opengenes-mcp-520634294170.us-central1.run.app/sse"
GENE_ONTOLOGY_MCP_URL = "https://gene-ontology-mcp-server-520634294170.us-central1.run.app/sse"

def create_agent(model: str = "gemini-2.5-pro") -> Agent:
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
