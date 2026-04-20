import os
from unittest.mock import MagicMock, patch

import pytest

# Prevent live MCP connections during import
os.environ.setdefault("BIOTECH_AGENT_AUTOLOAD", "false")


@pytest.fixture(autouse=True)
def mock_toolset():
    with patch("biotech_agent.utils.create_mcp_toolset", return_value=MagicMock()):
        yield


def test_create_normalization_agent():
    from biotech_agent.subagents.normalization.agent import create_agent
    agent = create_agent()
    assert agent.name == "normalization_agent"
    assert len(agent.tools) == 1


def test_create_gene_analysis_agent():
    from biotech_agent.subagents.gene_analysis.agent import create_agent
    agent = create_agent()
    assert agent.name == "gene_analysis_agent"
    assert len(agent.tools) == 2


def test_create_insight_synthesis_agent():
    from biotech_agent.subagents.insight_synthesis.agent import create_agent
    agent = create_agent()
    assert agent.name == "insight_synthesis_agent"
    assert len(agent.tools) == 1


def test_create_root_agent_has_three_subagents():
    from biotech_agent.agent import create_root_agent
    agent = create_root_agent()
    assert agent.name == "biotech_root_agent"
    assert len(agent.sub_agents) == 3


def test_root_agent_model_override():
    from biotech_agent.agent import create_root_agent
    agent = create_root_agent(model="gemini-1.5-flash")
    assert agent.model == "gemini-1.5-flash"
