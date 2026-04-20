import time
from unittest.mock import MagicMock, patch

import pytest

import biotech_agent.utils as utils_module
from biotech_agent.utils import (
    _audience_from_url,
    _fetch_token,
    create_mcp_toolset,
    get_auth_token,
)


@pytest.fixture(autouse=True)
def clear_token_cache():
    utils_module._token_cache.clear()
    yield
    utils_module._token_cache.clear()


# ---------------------------------------------------------------------------
# _audience_from_url
# ---------------------------------------------------------------------------

def test_audience_from_url_sse_path():
    assert _audience_from_url("https://foo.run.app/sse") == "https://foo.run.app"


def test_audience_from_url_no_sse():
    # Regression: old split('/sse')[0] would return the full URL here
    assert _audience_from_url("https://foo.run.app/api/v1") == "https://foo.run.app"


def test_audience_from_url_root():
    assert _audience_from_url("https://foo.run.app") == "https://foo.run.app"


# ---------------------------------------------------------------------------
# Token caching
# ---------------------------------------------------------------------------

def test_token_cache_hit():
    url = "https://cache-test.run.app/sse"
    with patch.object(utils_module, "_fetch_token", return_value="tok123") as mock_fetch:
        t1 = get_auth_token(url)
        t2 = get_auth_token(url)
    assert t1 == t2 == "tok123"
    mock_fetch.assert_called_once()  # second call served from cache


def test_token_cache_refresh_on_expiry():
    url = "https://expiry-test.run.app/sse"
    # Pre-populate cache with an already-expired entry
    utils_module._token_cache[url] = ("old_token", time.time() - 1)

    with patch.object(utils_module, "_fetch_token", return_value="new_token") as mock_fetch:
        token = get_auth_token(url)

    assert token == "new_token"
    mock_fetch.assert_called_once()


def test_token_cache_refresh_near_expiry():
    url = "https://near-expiry.run.app/sse"
    # Expires in 30s — within the 60s refresh window
    utils_module._token_cache[url] = ("soon_expired", time.time() + 30)

    with patch.object(utils_module, "_fetch_token", return_value="refreshed") as mock_fetch:
        token = get_auth_token(url)

    assert token == "refreshed"
    mock_fetch.assert_called_once()


# ---------------------------------------------------------------------------
# Empty gcloud token validation
# ---------------------------------------------------------------------------

def test_empty_gcloud_token_raises():
    with patch("subprocess.check_output", return_value=""):
        with pytest.raises(ValueError):
            _fetch_token("https://foo.run.app/sse")


# ---------------------------------------------------------------------------
# create_mcp_toolset retry logic
# ---------------------------------------------------------------------------

def test_create_mcp_toolset_succeeds_on_third_attempt():
    url = "https://retry-test.run.app/sse"

    call_count = 0

    def flaky_toolset(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ConnectionError("simulated failure")
        return MagicMock()

    with patch.object(utils_module, "get_auth_token", return_value="tok"), \
         patch("biotech_agent.utils.McpToolset", side_effect=flaky_toolset), \
         patch("biotech_agent.utils.SseConnectionParams", return_value=MagicMock()), \
         patch("time.sleep"):
        result = create_mcp_toolset(url)

    assert call_count == 3
    assert result is not None


def test_create_mcp_toolset_raises_after_max_retries():
    url = "https://fail-always.run.app/sse"

    with patch.object(utils_module, "get_auth_token", return_value="tok"), \
         patch("biotech_agent.utils.McpToolset", side_effect=ConnectionError("always fails")), \
         patch("biotech_agent.utils.SseConnectionParams", return_value=MagicMock()), \
         patch("time.sleep"):
        with pytest.raises(RuntimeError, match="Failed to connect MCP toolset"):
            create_mcp_toolset(url, max_retries=3)
