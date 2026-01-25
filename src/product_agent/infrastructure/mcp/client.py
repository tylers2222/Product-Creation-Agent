import inspect
from typing import List, Dict

import structlog
from langchain_mcp_adapters.client import MultiServerMCPClient  

logger = structlog.getLogger(__name__)

class MCPClient:
    """Class that defines retrieving MCP clients for servers"""
    def __init__(self, all_configs: Dict[str, Dict]):
        self.all_configs = all_configs
        self._cached_tools: Dict[str, list] = {}

    async def _check_exists(self, tool: str):
        """Check that a wanted tool has been initialised"""
        logger.debug("Starting %s", inspect.stack()[0][3])
        tools = self._cached_tools.get(tool, None)
        if tools is not None:
            logger.debug("Found in cache", tools=tools)

        return tools

    async def _get_tools_for_server(self, servers: list[str]):
        """Return the tools to an agent out of the MCP config"""
        logger.debug("Starting %s", inspect.stack()[0][3])
        tools = []
        for server in servers:
            logger.debug("Starting Servers Tool Gather", tool=server)
            tool_cached = await self._check_exists(server)
            if tool_cached is not None:
                tools.extend(tool_cached)
                continue
            
            logger.debug("Servers tools havent been cached")
            server_config = {server: self.all_configs[server]}
            client = MultiServerMCPClient(server_config)
            retrieved_tools = await client.get_tools()
            logger.debug("Retrieved tools from the server", tools=tools)
            tools.extend(retrieved_tools)

        return tools

    async def retrieve_agents_tools(self, servers: List[str]):
        """Callable by the main process"""
        logger.debug("Starting %s", inspect.stack()[0][3])
        tools_returned = await self._get_tools_for_server(servers=servers)
        logger.debug("Returned Tools For Agent", len_tools=len(tools_returned))
        return tools_returned

    async def add_config(self, config: List[Dict[str, Dict]]):
        # this may need a restart so need to check a time where nothing is being processed to be run potentially?
        # Not sure on an add feature, if platform like N8N being built, whats the go with adding while its live
        pass