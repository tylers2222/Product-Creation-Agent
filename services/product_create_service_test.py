"""
Tests for ShopifyProductCreateService.

Uses standardized TestCase pattern with data + expected results.
"""
import pytest
from pydantic import BaseModel

from services.product_create_service import ShopifyProductCreateService
from models.product_generation import QueryResponse
from services.schema import ProductExists


class TestMockShopifyProductCreateService:
    """Test an agentic workflows service layer using mock dependencies."""

    @pytest.fixture
    def workflow(self, mock_service_container):
        """Create service instance with mock dependencies."""
        return ShopifyProductCreateService(sc=mock_service_container, tools=None)

    #--------------------------------------------------------
    # Query Extract Node
    #--------------------------------------------------------

    def test_query_extract(self, workflow, tc_query_extract):
        """
        Test query extraction reformulates search query.

        Verifies:
        - Returns QueryResponse type
        - Brand name is title-cased
        - Product name is title-cased
        """
        tc = tc_query_extract

        result = workflow.query_extract(
            request_id=tc.data["request_id"],
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

    