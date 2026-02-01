from langchain.tools import tool
import pytest
from src.product_agent.config.agents.builder import AgentFactory
from src.product_agent.config.agents.config import AgentConfig

@tool
def add(x: int, y: int) -> int:
    """Add two numbers together."""
    return x + y

@pytest.mark.integration
class TestAgentBuilder:
    @pytest.fixture
    def factory(self, real_service_container):
        """Build the service container"""
        return AgentFactory(real_service_container)

    @pytest.fixture
    def agent_config(self):
        """Build a practice configuration for a custom agent"""
        return AgentConfig(
            name="Custom Agent",
            model="gpt-4o-mini",
            temperature=0.1,
            system_prompt=None,
            tools=[add]
        )

    @pytest.fixture
    def agent_config_not_supported(self):
        """Build a practice configuration for a custom agent but its not supported"""
        return AgentConfig(
            name="Custom Agent",
            model="oLlama-mini",
            temperature=0.1,
            system_prompt=None,
            tools=[add]
        )

    def test_building_custom(self, factory, agent_config):
        agent = factory.build_custom_agent(setup=agent_config)
        assert agent is not None

    def test_not_supported_llm(self, factory, agent_config_not_supported):
        with pytest.raises(ValueError):
            factory.build_custom_agent(agent_config_not_supported)