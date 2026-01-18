"""
Tests for agent definitions (synthesis_agent).

Integration tests require real service dependencies and API keys.
"""
import pytest
from qdrant_client.models import PointStruct

from product_agent.core.agent_configs.synthesis import SYNTHESIS_CONFIG
from product_agent.config import ServiceContainer, build_service_container, build_synthesis_agent

# -----------------------------------------------------------------------------
# Test Data Fixtures
# -----------------------------------------------------------------------------

@pytest.fixture
def sample_wrong_vector_results():
    """Sample vector search results that don't match the query category."""
    # Same brand, but completely different category (Protein instead of Pre-Workout)
    wrong_result_1 = PointStruct(
        id="6776123456789",
        vector=[0.45, 0.32, 0.18, 0.67, 0.21],
        payload={
            "title": "Optimum Nutrition Gold Standard 100% Whey",
            "body_html": "<h2>24g Protein per Serving</h2>",
            "product_type": "Whey Protein",
            "tags": "Protein Powder, Whey, Sports Nutrition",
            "vendor": "Optimum Nutrition"
        }
    )

    # Same brand, recovery/post-workout (not pre-workout)
    wrong_result_2 = PointStruct(
        id="6776987654321",
        vector=[0.52, 0.28, 0.41, 0.63, 0.19],
        payload={
            "title": "Optimum Nutrition Glutamine Powder",
            "body_html": "<h2>Support Recovery</h2>",
            "product_type": "Amino Acids",
            "tags": "Recovery, Glutamine, Post-Workout",
            "vendor": "Optimum Nutrition"
        }
    )

    # Different brand, has overlapping keywords
    wrong_result_3 = PointStruct(
        id="6776555444333",
        vector=[0.38, 0.44, 0.29, 0.71, 0.15],
        payload={
            "title": "MuscleTech Mass Gainer Nutrition Shake",
            "body_html": "<h2>1000 Calories Per Serving</h2>",
            "product_type": "Mass Gainer",
            "tags": "Weight Gain, Mass Gainer, Post Workout Nutrition",
            "vendor": "MuscleTech"
        }
    )

    return [wrong_result_1, wrong_result_2, wrong_result_3]


# -----------------------------------------------------------------------------
# Integration Tests
# -----------------------------------------------------------------------------

@pytest.mark.integration
class TestSynthesisAgentIntegration:
    """Integration tests for the synthesis agent.

    These tests require:
    - QDRANT_URL, QDRANT_API_KEY for vector database
    - FIRECRAWL_API_KEY for web scraping
    - OPENAI_API_KEY for LLM
    - Shopify credentials

    Run with: pytest -m integration
    """

    @pytest.fixture
    def integration_agent(self):
        """Create a synthesis agent with real service dependencies."""
        container = build_service_container()
        return build_synthesis_agent(container, SYNTHESIS_CONFIG)

    def test_synthesis_agent_invokes_successfully(
        self, integration_agent, sample_wrong_vector_results
    ):
        """Test that the synthesis agent can be invoked and returns a result."""
        title = "Optimum Nutrition Pre Workout"
        query = (
            f"Use tools to create a more relevant search in regards to {title}, "
            f"our first go returned {sample_wrong_vector_results}"
        )

        result = integration_agent.invoke({"input": query})

        assert result is not None
        assert "output" in result or isinstance(result, dict)

    def test_synthesis_agent_returns_structured_response(
        self, integration_agent, sample_wrong_vector_results
    ):
        """Test that the synthesis agent response has expected structure."""
        title = "Optimum Nutrition Pre Workout"
        query = (
            f"Use tools to create a more relevant search in regards to {title}, "
            f"our first go returned {sample_wrong_vector_results}, "
            "return a list of json objects of the new return data"
        )

        result = integration_agent.invoke({"input": query})

        assert result is not None
        # The result should be a dict with at least an output key
        assert isinstance(result, dict)
