# Biotech Agent AI — Comprehensive Improvement Plan

**Date:** 2026-04-20  
**Scope:** All critical issues in `biotech_agent/` core

---

## Requirements Summary

The codebase is a multi-agent biomedical research assistant built on Google ADK + Gemini 2.5 Pro with 4 MCP servers (OpenTargets, OpenGenes, Gene Ontology, OpenFDA) deployed on Cloud Run. The main `biotech_agent/` package (234 LOC) has several reliability, maintainability, and quality gaps that must be addressed without altering the external API or agent behavior.

---

## Acceptance Criteria

- [ ] All MCP server URLs are read from environment variables; zero hardcoded URLs remain in source
- [ ] `get_auth_token()` caches tokens and refreshes only when within 60s of expiry
- [ ] Audience extraction from URL is handled safely for paths other than `/sse`
- [ ] `create_mcp_toolset()` retries up to 3 times with exponential backoff on connection failure
- [ ] All subagents log at INFO level on creation and DEBUG level on tool invocation
- [ ] Model name is configurable via `BIOTECH_MODEL` environment variable with `gemini-2.5-pro` as fallback
- [ ] `root_agent` module-level instantiation is guarded so it does not run during import in test context
- [ ] Unit tests cover: token caching, URL audience extraction, retry logic, env-var config loading
- [ ] All existing agent behavior (tool routing, instruction prompts) is unchanged

---

## Implementation Steps

### Phase 1 — Configuration & Environment Variables

**Target:** `biotech_agent/subagents/*/agent.py`, `biotech_agent/agent.py`

#### Step 1.1 — Create `biotech_agent/config.py`

Create a central config module that reads all URLs and the model name from environment variables:

```python
# biotech_agent/config.py
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
```

#### Step 1.2 — Update subagents to import from config

- `normalization/agent.py:5` — remove `OPENTARGETS_MCP_URL = "..."`, import from `biotech_agent.config`
- `gene_analysis/agent.py:5-6` — remove both hardcoded URL constants, import from `biotech_agent.config`
- `insight_synthesis/agent.py:5` — remove `OPENFDA_MCP_URL = "..."`, import from `biotech_agent.config`
- `agent.py:6` — change default `model="gemini-2.5-pro"` to `model=DEFAULT_MODEL`

#### Step 1.3 — Add `.env.example` for the main agent

Add `OPENTARGETS_MCP_URL`, `OPENGENES_MCP_URL`, `GENE_ONTOLOGY_MCP_URL`, `OPENFDA_MCP_URL`, `BIOTECH_MODEL` to `biotech_agent/.env.example`.

---

### Phase 2 — Auth Token Caching & Safe URL Parsing

**Target:** `biotech_agent/utils.py`

#### Step 2.1 — Token caching with TTL

Current issue (`utils.py:46`): `get_auth_token()` is called once at toolset creation time and the token is captured in a closure (`utils.py:51`). Tokens expire but the closure never refreshes them.

Replace `get_auth_token` with a `TokenCache` class:

```python
import time
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class _CachedToken:
    token: str
    expires_at: float  # unix timestamp

_token_cache: dict[str, _CachedToken] = {}
_REFRESH_BEFORE_EXPIRY_SECS = 60

def get_auth_token(url: str) -> str:
    """Returns a cached OIDC token, refreshing if within 60s of expiry."""
    cached = _token_cache.get(url)
    if cached and time.time() < cached.expires_at - _REFRESH_BEFORE_EXPIRY_SECS:
        return cached.token
    token = _fetch_token(url)
    # Cloud Run OIDC tokens are valid for 1 hour
    _token_cache[url] = _CachedToken(token=token, expires_at=time.time() + 3600)
    return token
```

Move the existing subprocess/google.auth logic into `_fetch_token(url)`.

#### Step 2.2 — Safe audience URL extraction

Current issue (`utils.py:36`): `url.split('/sse')[0]` silently returns the full URL if the path is not exactly `/sse`.

Replace with:

```python
from urllib.parse import urlparse

def _audience_from_url(url: str) -> str:
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"
```

#### Step 2.3 — Validate gcloud token output

Current issue (`utils.py:22-25`): `subprocess.check_output(...)` could return an empty string without raising.

Add: `if not token: raise ValueError("gcloud returned empty token")`

#### Step 2.4 — Refresh token in `header_provider`

Current issue (`utils.py:47-51`): The `header_provider` closure captures the token at creation time and never refreshes it.

Change it to call `get_auth_token(url)` at invocation time (safe now that caching is in place):

```python
def header_provider(_context=None) -> dict[str, str]:
    return {"Authorization": f"Bearer {get_auth_token(url)}"}
```

---

### Phase 3 — Retry Logic for MCP Connections

**Target:** `biotech_agent/utils.py:43-63`

#### Step 3.1 — Add retry wrapper to `create_mcp_toolset`

Wrap `McpToolset(...)` construction in a retry loop with exponential backoff:

```python
import time

def create_mcp_toolset(url: str, max_retries: int = 3) -> McpToolset:
    last_exc = None
    for attempt in range(max_retries):
        try:
            token = get_auth_token(url)
            connection_params = SseConnectionParams(
                url=url,
                headers={"Authorization": f"Bearer {token}"},
                timeout=30.0,
                sse_read_timeout=300.0
            )
            toolset = McpToolset(
                connection_params=connection_params,
                header_provider=lambda _ctx=None: {"Authorization": f"Bearer {get_auth_token(url)}"}
            )
            logger.info(f"MCP toolset connected: {url}")
            return toolset
        except Exception as exc:
            last_exc = exc
            wait = 2 ** attempt
            logger.warning(f"MCP connect attempt {attempt+1}/{max_retries} failed for {url}: {exc}. Retrying in {wait}s")
            time.sleep(wait)
    raise RuntimeError(f"Failed to connect MCP toolset after {max_retries} attempts: {url}") from last_exc
```

---

### Phase 4 — Structured Logging

**Target:** All subagent `agent.py` files and root `agent.py`

#### Step 4.1 — Add logger to each subagent

Each `create_agent()` function should log at creation:

```python
import logging
logger = logging.getLogger(__name__)

def create_agent(model: str = DEFAULT_MODEL) -> Agent:
    logger.info("Creating normalization_agent with model=%s url=%s", model, OPENTARGETS_MCP_URL)
    ...
```

#### Step 4.2 — Log root agent orchestration start

In `agent.py`, log when `create_root_agent()` is called and which sub-agents are included.

---

### Phase 5 — Guard Module-Level Instantiation

**Target:** `biotech_agent/agent.py:35`

Current issue: `root_agent = create_root_agent()` runs at import time, which triggers MCP connections whenever the module is imported (including during tests or `import biotech_agent.agent` in notebooks).

Change to:

```python
# Only instantiate when run directly or explicitly requested
import os
if os.environ.get("BIOTECH_AGENT_AUTOLOAD", "true").lower() == "true":
    root_agent = create_root_agent()
```

Tests set `BIOTECH_AGENT_AUTOLOAD=false` to skip live connections.

---

### Phase 6 — Unit Tests

**Target:** new `biotech_agent/tests/` directory

#### Step 6.1 — `tests/test_config.py`

- Verify each URL config reads from env var when set
- Verify fallback to default value when env var is absent
- Verify `DEFAULT_MODEL` reads from `BIOTECH_MODEL`

#### Step 6.2 — `tests/test_utils.py`

- `test_audience_from_url`: assert `_audience_from_url("https://foo.run.app/sse")` == `"https://foo.run.app"`
- `test_audience_from_url_no_sse`: assert `_audience_from_url("https://foo.run.app/api/v1")` == `"https://foo.run.app"` (regression on old split logic)
- `test_token_cache_hit`: after first call, second call with same URL should not call `_fetch_token` again
- `test_token_cache_refresh`: expired token (mock `time.time`) triggers `_fetch_token`
- `test_empty_gcloud_token_raises`: mock subprocess returning `""` should raise `ValueError`
- `test_create_mcp_toolset_retries`: mock `McpToolset` to raise on first 2 attempts, succeed on 3rd; assert 3 calls total

#### Step 6.3 — `tests/test_agents.py`

- Mock `create_mcp_toolset` to return `MagicMock()`
- Assert `create_normalization_agent()` returns an `Agent` with `name="normalization_agent"`
- Assert `create_gene_analysis_agent()` returns an `Agent` with 2 tools
- Assert `create_root_agent()` returns an `Agent` with 3 sub-agents

---

## Risks and Mitigations

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Token cache causes stale tokens in long-running processes | Medium | 60s refresh buffer before expiry; token TTL set conservatively to 3600s (actual Cloud Run OIDC TTL) |
| `BIOTECH_AGENT_AUTOLOAD=false` not set in existing deploy scripts | Low | Default is `"true"` so existing deployments are unaffected |
| Retry backoff delays agent startup in degraded network | Low | Max 3 retries = max 6s delay; acceptable for startup |
| URL audience extraction breaks for non-standard Cloud Run URLs | Low | `urlparse` is stdlib and handles all RFC-3986 URLs correctly |

---

## Verification Steps

1. `BIOTECH_AGENT_AUTOLOAD=false python -c "import biotech_agent.agent"` — must complete without network calls
2. `python -m pytest biotech_agent/tests/ -v` — all tests pass
3. `grep -r "https://opentargets-mcp\|https://opengenes\|https://gene-ontology\|https://openfda" biotech_agent/` — zero matches in subagent files (only in config.py defaults)
4. Set a fake URL via env var, run agent creation — must fail at connection, not at import
5. Mock network failure for first 2 attempts — agent must connect on 3rd attempt and log 2 warnings
