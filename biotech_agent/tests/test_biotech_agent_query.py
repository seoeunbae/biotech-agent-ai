import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from biotech_agent.agent import BioTechAgent

@pytest.fixture
def mock_biotech_agent():
    with patch('biotech_agent.agent.create_root_agent') as mock_create_root_agent:
        mock_root_agent_instance = MagicMock()
        
        # Mock run method to be awaitable
        mock_root_agent_instance.run = AsyncMock(return_value="Direct Mocked Root Agent Result")
        
        # Mock stream method to be an async generator
        async def async_generator_mock(*args, **kwargs):
            for item in ["Direct", "Mocked", "Stream"]:
                yield item
        mock_root_agent_instance.stream.return_value = async_generator_mock()

        mock_create_root_agent.return_value = mock_root_agent_instance
        
        agent = BioTechAgent()
        agent.agent = mock_root_agent_instance # Ensure the instance uses our mock
        yield agent

class TestBioTechAgent:

    @pytest.mark.asyncio
    async def test_async_query(self, mock_biotech_agent):
        query_input = "test query"
        result = await mock_biotech_agent.async_query(query_input)
        
        assert result == "Direct Mocked Root Agent Result"
        mock_biotech_agent.agent.run.assert_called_once_with(query_input)

    @pytest.mark.asyncio
    async def test_async_stream_query(self, mock_biotech_agent):
        query_input = "test query for streaming"
        
        chunks = []
        async for chunk in mock_biotech_agent.async_stream_query(query_input):
            chunks.append(chunk)

        expected_chunks = ["Direct", "Mocked", "Stream"]
        assert chunks == expected_chunks
        mock_biotech_agent.agent.stream.assert_called_once_with(query_input)

