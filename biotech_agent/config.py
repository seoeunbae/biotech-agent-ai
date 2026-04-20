import os

OPENTARGETS_MCP_URL = os.environ.get(
    "OPENTARGETS_MCP_URL",
    "https://opentargets-mcp-520634294170.us-central1.run.app/sse"
)
OPENGENES_MCP_URL = os.environ.get(
    "OPENGENES_MCP_URL",
    "https://opengenes-mcp-520634294170.us-central1.run.app/sse"
)
GENE_ONTOLOGY_MCP_URL = os.environ.get(
    "GENE_ONTOLOGY_MCP_URL",
    "https://gene-ontology-mcp-server-520634294170.us-central1.run.app/sse"
)
OPENFDA_MCP_URL = os.environ.get(
    "OPENFDA_MCP_URL",
    "https://openfda-mcp-server-520634294170.us-central1.run.app/sse"
)
DEFAULT_MODEL = os.environ.get("BIOTECH_MODEL", "gemini-2.5-pro")
