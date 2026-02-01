import pytest


from product_agent.core.agent_configs.scraper import SCRAPER_AGENT_SYSTEM_PROMPT

class TestSystemPrompts:
    @pytest.fixture
    def scraper_system_propmt(self):
        return SCRAPER_AGENT_SYSTEM_PROMPT

    def test_length_isnt_zero(self, scraper_system_propmt):
        """Testing that our system prompt isnt empty or deleted"""
        length = len(scraper_system_propmt)
        assert length > 0
        print("Length Of System Prompt: ", length)
        print("Tokens System Prompt: ", length / 4)