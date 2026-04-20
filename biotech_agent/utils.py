import logging
import subprocess
import time
from typing import Dict
from urllib.parse import urlparse

import google.auth
import google.auth.transport.requests
from google.oauth2 import id_token
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import SseConnectionParams

logger = logging.getLogger(__name__)

# Token cache: url -> (token, expires_at)
_token_cache: Dict[str, tuple[str, float]] = {}
_TOKEN_TTL_SECS = 3600
_REFRESH_BEFORE_EXPIRY_SECS = 60


def _audience_from_url(url: str) -> str:
    """Extracts the base service URL to use as OIDC audience."""
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


def _fetch_token(url: str) -> str:
    """Fetches a fresh OIDC token for the given URL."""
    try:
        token = subprocess.check_output(
            ["gcloud", "auth", "print-identity-token"], text=True
        ).strip()
    except Exception as e_gcloud:
        logger.debug("gcloud auth failed, falling back to google.auth: %s", e_gcloud)
    else:
        if not token:
            raise ValueError("gcloud returned empty token")
        return token

    try:
        auth_req = google.auth.transport.requests.Request()
        audience = _audience_from_url(url)
        token = id_token.fetch_id_token(auth_req, audience)
        return token
    except Exception as e:
        logger.warning("Failed to generate ID token for %s: %s", url, e)
        raise


def get_auth_token(url: str) -> str:
    """Returns a cached OIDC token, refreshing if within 60s of expiry."""
    cached = _token_cache.get(url)
    if cached:
        token, expires_at = cached
        if time.time() < expires_at - _REFRESH_BEFORE_EXPIRY_SECS:
            return token

    token = _fetch_token(url)
    _token_cache[url] = (token, time.time() + _TOKEN_TTL_SECS)
    logger.debug("Fetched fresh OIDC token for %s", url)
    return token


def create_mcp_toolset(url: str, max_retries: int = 3) -> McpToolset:
    """Creates an McpToolset connected to the given SSE URL with OIDC auth and retry logic."""
    last_exc: Exception | None = None

    for attempt in range(max_retries):
        try:
            token = get_auth_token(url)
            connection_params = SseConnectionParams(
                url=url,
                headers={"Authorization": f"Bearer {token}"},
                timeout=30.0,
                sse_read_timeout=300.0,
            )
            toolset = McpToolset(
                connection_params=connection_params,
                header_provider=lambda _ctx=None, _url=url: {
                    "Authorization": f"Bearer {get_auth_token(_url)}"
                },
            )
            logger.info("MCP toolset connected: %s", url)
            return toolset
        except Exception as exc:
            last_exc = exc
            wait = 2 ** attempt
            logger.warning(
                "MCP connect attempt %d/%d failed for %s: %s. Retrying in %ds",
                attempt + 1, max_retries, url, exc, wait,
            )
            time.sleep(wait)

    raise RuntimeError(
        f"Failed to connect MCP toolset after {max_retries} attempts: {url}"
    ) from last_exc
