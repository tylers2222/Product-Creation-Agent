"""
Tests for ShopifyProductCreateService.

Uses standardized TestCase pattern with data + expected results.
"""
import pytest
from pydantic import BaseModel

from product_agent.services.agent_workflows.product_creation import ShopifyProductCreateService
from product_agent.models.query import QueryResponse
from product_agent.services.schemas import ProductExists
from tests.mocks.synthesis_mock import MockSynthesisAgent
from product_agent.infrastructure.synthesis.agent import SynthesisAgent
from product_agent.core.agent_configs.synthesis import SYNTHESIS_CONFIG

from product_agent.config.agents import build_synthesis_agent


class TestMockShopifyProductCreateService:
    """Test an agentic workflows service layer using mock dependencies."""

    @pytest.fixture
    def workflow(self, mock_service_container):
        """Create service instance with mock dependencies."""
        return ShopifyProductCreateService(sc=mock_service_container, synthesis_agent=MockSynthesisAgent())

    #--------------------------------------------------------
    # Query Extract Node
    #--------------------------------------------------------

    @pytest.mark.asyncio
    async def test_query_extract(self, workflow, tc_query_extract):
        """
        Test query extraction reformulates search query.

        Verifies:
        - Returns QueryResponse type
        - Brand name is title-cased
        - Product name is title-cased
        """
        tc = tc_query_extract

        result = await workflow.query_extract(
            query=tc.data["query"]
        )

        # Assert type
        assert isinstance(result, tc.expected["type"])

        # Assert the query was modified (brand/product names title-cased in the function)
        assert tc.data["query"].brand_name == tc.expected["brand_name_title_cased"]
        assert tc.data["query"].product_name == tc.expected["product_name_title_cased"]

    #--------------------------------------------------------
    # Query Already Exists Node
    #--------------------------------------------------------

    @pytest.mark.asyncio
    async def test_check_if_product_already_exists_found_by_sku(
        self, workflow, tc_check_product_exists_found_by_sku
    ):
        """
        Test product existence check when SKU matches.

        Verifies:
        - Returns ProductExists type
        - Method is 'shopify'
        - Product name is populated
        """
        tc = tc_check_product_exists_found_by_sku

        result = await workflow.check_if_product_already_exists(
            query=tc.data["query"]
        )

        if tc.expected["product_exists"]:
            print("Tc: ", tc)
            assert result is not None
            assert isinstance(result, tc.expected["type"])
            assert result.method == tc.expected["method"]
            assert result.product_name is not None

    @pytest.mark.asyncio
    async def test_check_if_product_already_exists_found_by_vector(
        self, workflow, tc_check_product_exists_found_by_vector
    ):
        """
        Test product existence check when vector similarity exceeds threshold.

        Verifies:
        - Returns ProductExists type
        - Method is 'vector_search'
        - Score exceeds minimum threshold
        """
        tc = tc_check_product_exists_found_by_vector

        result = await workflow.check_if_product_already_exists(
            query=tc.data["query"]
        )

        if tc.expected["product_exists"]:
            assert result is not None
            assert isinstance(result, tc.expected["type"])
            print("This is the method 1 line before assert: ", tc.expected["method"])
            assert result.method == tc.expected["method"]
            assert result.score >= tc.expected["min_score"]

    @pytest.mark.asyncio
    async def test_check_if_product_already_exists_not_found(
        self, workflow, tc_check_product_exists_not_found
    ):
        """
        Test product existence check when product doesn't exist.

        Verifies:
        - Returns None
        """
        tc = tc_check_product_exists_not_found

        result = await workflow.check_if_product_already_exists(
            query=tc.data["query"]
        )

        if not tc.expected["product_exists"]:
            assert result is None

    
    #--------------------------------------------------------
    # Query Scrape Node
    #--------------------------------------------------------

    def test_scrape(self, workflow):
        scraper_response = workflow.query_scrape(query="Optimum Nutrition Creatine +")
        assert scraper_response is not None
        assert isinstance(scraper_response, BaseModel)
        assert len(scraper_response.result) > 0

    #--------------------------------------------------------
    # Query Synthesis Node
    #--------------------------------------------------------

    def test_query_synthesis(self, workflow, tc_query_synthesis_low_relevance):
        tc = tc_query_synthesis_low_relevance

        synthesis_response = workflow.query_synthesis(query=tc.data["query"], similar_products=tc.data["similar_products"])
        assert len(synthesis_response.similar_products) > 0



# --------------------------------------------------------------------------
# Integration Tests
# --------------------------------------------------------------------------

class TestIntegrationProductCreateWorkflow:
    """Test an agentic worflow with real integrations"""
    @pytest.fixture
    def integration_workflow(self, service_container):
        agent_executor = build_synthesis_agent(service_container, SYNTHESIS_CONFIG)
        return ShopifyProductCreateService(sc=service_container, synthesis_agent=SynthesisAgent(agent_executor))

    @pytest.mark.integration
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

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_check_if_product_already_exists_no_shopify(self, integration_workflow, tc_check_product_exists_found_by_vector):
        tc = tc_check_product_exists_found_by_vector
        tc_query = tc.data["query"]

        product_exists = await integration_workflow.check_if_product_already_exists(query=tc_query)
        assert product_exists is None

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_check_if_product_already_exists_shopify(self, integration_workflow, tc_check_product_exists_found_by_sku):
        tc = tc_check_product_exists_found_by_sku
        tc_query = tc.data["query"]

        product_exists = await integration_workflow.check_if_product_already_exists(query=tc_query)
        assert product_exists is not None
        assert isinstance(product_exists, tc.expected["type"])
        assert product_exists.product_name == tc.expected["product"]
        assert product_exists.method == tc.expected["method"]

    @pytest.mark.integration
    def test_scrape_and_synthesis(self, integration_workflow):
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

    @pytest.mark.integration
    def test_vector_synthesis(self, integration_workflow, tc_query_synthesis_high_relevance):
        query = "Optimum Nutrition Gold Standard Whey"

        tc = tc_query_synthesis_high_relevance

        similar_products = tc.data["similar_products"]
        assert similar_products is not None

        vector_relevance = integration_workflow.query_synthesis(query=query, similar_products=similar_products)
        assert vector_relevance is not None
        assert len(vector_relevance.similar_products) > 0
        assert vector_relevance.action_taken