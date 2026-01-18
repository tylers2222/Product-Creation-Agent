"""
Tests for the ShopifyProductWorkflow agent.

Unit tests use mock dependencies, integration tests use real services.
"""
import pytest
import uuid

from product_agent.core.workflow import ShopifyProductWorkflow
from product_agent.infrastructure.llm.prompts import format_product_input, PromptVariant
from product_agent.infrastructure.shopify.schemas import Option, Variant, InventoryAtStores
from product_agent.config import ServiceContainer, build_service_container


# -----------------------------------------------------------------------------
# Test Data Fixtures
# -----------------------------------------------------------------------------

@pytest.fixture
def sample_prompt_variant():
    """Sample product input for testing the workflow."""
    option_size_50g = Option(option_name="Size", option_value="50 g")
    option_flavour_choc = Option(option_name="Flavour", option_value="White Choc Caramel")

    variants = [
        Variant(
            option1_value=option_size_50g,
            option2_value=option_flavour_choc,
            sku=922026,
            barcode="0810095637971",
            price=4.95,
            product_weight=0.05,
            inventory_at_stores=InventoryAtStores(city=15, south_melbourne=15)
        ),
    ]

    return PromptVariant(
        brand_name="EHP",
        product_name="Oxyshred Protein Lean Bar",
        variants=variants
    )


@pytest.fixture
def workflow_with_mocks(mock_shop, mock_scraper, mock_vector_db, mock_embeddor, mock_llm):
    """Create a ShopifyProductWorkflow with all mock dependencies."""
    container = ServiceContainer(
        shop=mock_shop,
        scraper=mock_scraper,
        vector_db=mock_vector_db,
        embeddor=mock_embeddor,
        llm=mock_llm
    )

    return ShopifyProductWorkflow(container=container)


# -----------------------------------------------------------------------------
# Unit Tests
# -----------------------------------------------------------------------------

class TestShopifyProductWorkflow:
    """Unit tests for ShopifyProductWorkflow using mock dependencies."""

    def test_workflow_initialization(self, workflow_with_mocks):
        """Test that the workflow initializes correctly with mock dependencies."""
        assert workflow_with_mocks is not None

    def test_format_product_input(self, sample_prompt_variant):
        """Test that format_product_input produces valid query string."""
        query = format_product_input(prompt_variant=sample_prompt_variant)

        assert query is not None
        assert len(query) > 0
        assert "EHP" in query or "Oxyshred" in query

    def test_format_product_input_includes_inventory(self, sample_prompt_variant):
        """Test that format_product_input includes inventory information."""
        query = format_product_input(prompt_variant=sample_prompt_variant)

        # The query should contain inventory information
        assert "15" in query or "inventory" in query.lower()


# -----------------------------------------------------------------------------
# Integration Tests
# -----------------------------------------------------------------------------

@pytest.mark.integration
class TestShopifyProductWorkflowIntegration:
    """Integration tests for ShopifyProductWorkflow using real services.

    These tests require environment variables to be set:
    - SHOPIFY_API_KEY, SHOPIFY_API_SECRET, SHOPIFY_TOKEN
    - FIRECRAWL_API_KEY
    - QDRANT_URL, QDRANT_API_KEY
    - OPENAI_API_KEY

    Run with: pytest -m integration
    Skip with: pytest -m "not integration"
    """

    @pytest.fixture
    def integration_workflow(self):
        """Create a workflow with real service dependencies."""
        container = build_service_container()
        return ShopifyProductWorkflow(container=container)

    @pytest.mark.asyncio
    async def test_service_workflow_runs(self, integration_workflow, sample_prompt_variant):
        """Test that the full workflow executes without errors."""
        query = format_product_input(prompt_variant=sample_prompt_variant)
        request_id = str(uuid.uuid4())

        result = await integration_workflow.service_workflow(
            query=query,
            request_id=request_id
        )

        assert result is not None
        assert hasattr(result, 'url') or hasattr(result, 'id')
