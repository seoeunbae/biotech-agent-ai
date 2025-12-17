import asyncio
import logging
import sys
from biotech_agent.utils import create_mcp_toolset

# Configure logging to see what's happening
logging.basicConfig(level=logging.DEBUG)

OPENTARGETS_MCP_URL = "https://opentargets-mcp-520634294170.us-central1.run.app/sse"

async def verify_connection():
    print(f"Connecting to {OPENTARGETS_MCP_URL}...")
    # Manually create toolset with headers in connection params to verified fix
    from biotech_agent.utils import get_auth_token
    from google.adk.tools import McpToolset
    from google.adk.tools.mcp_tool.mcp_session_manager import SseConnectionParams
    
    # Try basic gcloud token without audience
    import subprocess
    try:
        token = subprocess.check_output(
            ["gcloud", "auth", "print-identity-token"], text=True
        ).strip()
        print("Got token from gcloud (no audience)")
    except Exception as e:
        print(f"gcloud failed: {e}")
        from biotech_agent.utils import get_auth_token
        token = get_auth_token(OPENTARGETS_MCP_URL)
    
    # Debug: Check token claims
    import json
    import base64
    try:
        # JWT is header.payload.signature
        payload = token.split('.')[1]
        # Add padding
        payload += '=' * (-len(payload) % 4)
        decoded = json.loads(base64.b64decode(payload))
        print(f"Token Audience (aud): {decoded.get('aud')}")
        print(f"Token Issuer (iss): {decoded.get('iss')}")
    except Exception as e:
        print(f"Failed to decode token: {e}")

    # Debug: Try curl
    import subprocess
    print("Trying curl...")
    try:
        subprocess.run([
            "curl", "-v", OPENTARGETS_MCP_URL,
            "-H", f"Authorization: Bearer {token}"
        ], check=False)
    except Exception as e:
        print(f"Curl failed: {e}")

    connection_params = SseConnectionParams(
        url=OPENTARGETS_MCP_URL,
        headers={"Authorization": f"Bearer {token}"},
        timeout=30.0, 
        sse_read_timeout=300.0
    )
    toolset = McpToolset(connection_params=connection_params)
    
    print("Fetching tools...")
    try:
        tools = await toolset.get_tools()
        print(f"Successfully retrieved {len(tools)} tools.")
        for tool in tools:
            print(f"- {tool.name}: {tool.description}")
            
    except Exception as e:
        print(f"Error fetching tools: {e}")
        raise e

if __name__ == "__main__":
    try:
        asyncio.run(verify_connection())
    except Exception as e:
        print(f"Verification failed: {e}")
        sys.exit(1)
