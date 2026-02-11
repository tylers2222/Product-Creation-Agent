import pytest
from pydantic import BaseModel

from product_agent.services.agent_workflows.product_creation import ShopifyProductCreateService
from product_agent.models.query import QueryResponse
from product_agent.infrastructure.synthesis.agent import SynthesisAgent
from product_agent.core.agent_configs.synthesis import SYNTHESIS_CONFIG

from product_agent.config.agents import build_synthesis_agent

# --------------------------------------------------------------------------
# Integration Tests
# --------------------------------------------------------------------------

@pytest.mark.integration
class TestIntegrationProductCreateWorkflow:
    """Test an agentic worflow with real integrations"""
    @pytest.fixture
    def integration_workflow(self, service_container):
        agent_executor = build_synthesis_agent(service_container, SYNTHESIS_CONFIG)
        return ShopifyProductCreateService(sc=service_container, synthesis_agent=SynthesisAgent(agent_executor))

    @pytest.mark.asyncio
    async def test_query_extract(self, integration_workflow, tc_query_extract):
        """Integration test for query extract"""
        tc = tc_query_extract
        tc_query = tc.data["query"]
        # print("Query: ", tc_query)

        result = await integration_workflow.query_extract(
            query=tc_query
        )

        assert isinstance(result, QueryResponse)
        assert result.adapted_search_string

    @pytest.mark.asyncio
    async def test_check_if_product_already_exists_no_shopify(self, integration_workflow, tc_check_product_exists_found_by_vector):
        """Integration test for checking product existence when not found in Shopify"""
        tc = tc_check_product_exists_found_by_vector
        tc_query = tc.data["query"]

        product_exists = await integration_workflow.check_if_product_already_exists(query=tc_query)
        assert product_exists is None

    @pytest.mark.asyncio
    async def test_check_if_product_already_exists_shopify(self, integration_workflow, tc_check_product_exists_found_by_sku):
        """Integration test for checking product existence when found in Shopify"""
        tc = tc_check_product_exists_found_by_sku
        tc_query = tc.data["query"]

        product_exists = await integration_workflow.check_if_product_already_exists(query=tc_query)
        assert product_exists is not None
        assert isinstance(product_exists, tc.expected["type"])
        assert product_exists.product_name == tc.expected["product"]
        assert product_exists.method == tc.expected["method"]

    def test_scrape_and_synthesis(self, integration_workflow):
        """Integration test for scraping and synthesizing product data"""
        query = "Optimum Nutrition Gold Standard Whey"
        query_for_search = "Optimum Nutrition Gold Standard Whey buy online"

        #for logger in logging.Logger.manager.loggerDict:
            #print(logger)

        scraper_and_vector_search = integration_workflow.query_scrape(query=query_for_search)
        assert scraper_and_vector_search is not None

        scraper_response = scraper_and_vector_search[0]
        assert len(scraper_response.result) > 1
        assert scraper_response.all_success

        vector_response = scraper_and_vector_search[1]
        assert vector_response is not None
        assert len(vector_response) > 0

        vector_relevance = integration_workflow.query_synthesis(query=query, similar_products=vector_response)
        assert vector_relevance is not None
        assert len(vector_relevance.similar_products) > 0
        assert vector_relevance.action_taken

    def test_vector_synthesis(self, integration_workflow, tc_query_synthesis_high_relevance):
        """Integration test for vector similarity synthesis with high relevance products"""
        query = "Optimum Nutrition Gold Standard Whey"

        tc = tc_query_synthesis_high_relevance

        similar_products = tc.data["similar_products"]
        assert similar_products is not None

        vector_relevance = integration_workflow.query_synthesis(query=query, similar_products=similar_products)
        assert vector_relevance is not None
        assert len(vector_relevance.similar_products) > 0
        assert vector_relevance.action_taken