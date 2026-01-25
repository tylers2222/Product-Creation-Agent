import pytest

from src.product_agent.infrastructure.mcp.client import MCPClient
from src.product_agent.infrastructure.mcp.config import MCP_SERVER_CONFIG

class TestMCPConnection:
    @pytest.fixture
    def get_mcp_client(self):
        return MCPClient(MCP_SERVER_CONFIG)

    @pytest.mark.asyncio
    async def test_retrieve_agent_tools(self, get_mcp_client):
        """Testing getting a list of tools"""
        tools = await get_mcp_client.retrieve_agents_tools(servers=[key for key in MCP_SERVER_CONFIG.keys()])
        assert tools is not None
        assert len(tools) > 0
        print("Tool Type: ", type(tools[0]))
        for tool in tools:
            print(f"\n {tool}")