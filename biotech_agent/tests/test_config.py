import os
import sys


def _reload_config(env: dict):
    """Reload biotech_agent.config with the given env vars set."""
    for mod in list(sys.modules):
        if "biotech_agent.config" in mod:
            del sys.modules[mod]
    old_env = {k: os.environ.get(k) for k in env}
    os.environ.update(env)
    try:
        import biotech_agent.config as cfg
        return cfg
    finally:
        for k, v in old_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def test_opentargets_url_from_env():
    cfg = _reload_config({"OPENTARGETS_MCP_URL": "https://custom-opentargets.example.com/sse"})
    assert cfg.OPENTARGETS_MCP_URL == "https://custom-opentargets.example.com/sse"


def test_opentargets_url_default():
    for mod in list(sys.modules):
        if "biotech_agent.config" in mod:
            del sys.modules[mod]
    os.environ.pop("OPENTARGETS_MCP_URL", None)
    import biotech_agent.config as cfg
    assert "opentargets-mcp" in cfg.OPENTARGETS_MCP_URL


def test_default_model_from_env():
    cfg = _reload_config({"BIOTECH_MODEL": "gemini-1.5-flash"})
    assert cfg.DEFAULT_MODEL == "gemini-1.5-flash"


def test_default_model_fallback():
    for mod in list(sys.modules):
        if "biotech_agent.config" in mod:
            del sys.modules[mod]
    os.environ.pop("BIOTECH_MODEL", None)
    import biotech_agent.config as cfg
    assert cfg.DEFAULT_MODEL == "gemini-2.5-pro"


def test_all_urls_configurable():
    cfg = _reload_config({
        "OPENTARGETS_MCP_URL": "https://a.example.com/sse",
        "OPENGENES_MCP_URL": "https://b.example.com/sse",
        "GENE_ONTOLOGY_MCP_URL": "https://c.example.com/sse",
        "OPENFDA_MCP_URL": "https://d.example.com/sse",
    })
    assert cfg.OPENTARGETS_MCP_URL == "https://a.example.com/sse"
    assert cfg.OPENGENES_MCP_URL == "https://b.example.com/sse"
    assert cfg.GENE_ONTOLOGY_MCP_URL == "https://c.example.com/sse"
    assert cfg.OPENFDA_MCP_URL == "https://d.example.com/sse"
