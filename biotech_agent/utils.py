import logging
import os
from typing import Optional, Dict

import google.auth
import google.auth.transport.requests
from google.oauth2 import id_token
from google.adk.tools import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import SseConnectionParams
from google.adk.agents.readonly_context import ReadonlyContext

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_auth_token(url: str) -> str:
    """Generates OIDC token for the given URL."""
    # Try gcloud first as it might have better user credentials than ADC in this env
    try:
        import subprocess
        # logger.info("Attempting to get token via gcloud...")
        token = subprocess.check_output(
            ["gcloud", "auth", "print-identity-token"], text=True
        ).strip()
        return token
    except Exception as e_gcloud:
        logger.debug(f"gcloud auth failed, falling back to google.auth: {e_gcloud}")

    try:
        auth_req = google.auth.transport.requests.Request()
        # For Cloud Run, we usually use the target audience as the URL
        # We might need to trim the URL to just the base URL if it has paths, but usually the full URL is fine or the service URL.
        # Cloud Run audience is usually the service URL (e.g. https://service-hash.run.app)
        # The URLs we have are like https://.../sse
        # We should probably use the root URL as audience.
        audience = url.split('/sse')[0]
        token = id_token.fetch_id_token(auth_req, audience)
        return token
    except Exception as e:
        logger.warning(f"Failed to generate ID token for {url}: {e}")
        raise e

def create_mcp_toolset(url: str) -> McpToolset:
    """Creates an McpToolset connected to the given SSE URL with OIDC auth."""
    
    token = get_auth_token(url)
    def header_provider(_context: Optional[ReadonlyContext] = None) -> Dict[str, str]:
        # Regenerate token if needed for fresh calls, though simple bearer might suffice if long-lived
        # For now, just return the captured token to match connection or fetch new if expired logic logic was added
        # But simply:
        return {"Authorization": f"Bearer {token}"}

    connection_params = SseConnectionParams(
        url=url,
        headers={"Authorization": f"Bearer {token}"},
        timeout=30.0, 
        sse_read_timeout=300.0
    )
    
    return McpToolset(
        connection_params=connection_params,
        header_provider=header_provider
    )
