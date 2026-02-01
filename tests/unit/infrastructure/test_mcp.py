import pytest

from src.product_agent.infrastructure.mcp.client import MCPClient
from src.product_agent.infrastructure.mcp.config import mcp_server_config

class TestMCPConnection:
    @pytest.fixture
    def get_mcp_client(self):
        config = mcp_server_config()
        return MCPClient(config)

    @pytest.mark.asyncio
    async def test_retrieve_agent_tools(self, get_mcp_client):
        """Testing getting a list of tools"""
        config = mcp_server_config()
        tools = await get_mcp_client.retrieve_agents_tools(servers=[key for key in config.keys()])
        assert tools is not None
        assert len(tools) > 0
        print("Tool Type: ", type(tools[0]))
        for tool in tools:
            print(f"\n {tool}")