"""
Tests for Shopify API client.

Unit tests use mock client, integration tests use real Shopify API.
"""
import pytest
import os
from dotenv import load_dotenv
import asyncio

from agents.infrastructure.shopify_api.product_schema import (
    DraftProduct, DraftResponse, Variant, Option, InventoryAtStores
)
from agents.infrastructure.shopify_api.schema import Inventory, Inputs
from agents.infrastructure.shopify_api.client import (
            ShopifyClient, Locations, Location
        )


# -----------------------------------------------------------------------------
# Test Data Fixtures
# -----------------------------------------------------------------------------

@pytest.fixture
def draft_product_with_one_option():
    """Fixture for a draft product with a single option (Size)."""
    variant1 = Variant(
        option1_value=Option(option_name="Size", option_value="2kg"),
        sku=561596,
        barcode=9238957523,
        price=64.95,
        compare_at=79.95,
        product_weight=1.0,
        inventory_at_stores=InventoryAtStores(city=45, south_melbourne=28)
    )
    variant2 = Variant(
        option1_value=Option(option_name="Size", option_value="1kg"),
        sku=561597,
        barcode=9233952523,
        price=119.95,
        compare_at=149.95,
        product_weight=2.0,
        inventory_at_stores=InventoryAtStores(city=45, south_melbourne=28)
    )

    return DraftProduct(
        title="Gold Standard 100% Whey Protein - Double Rich Chocolate",
        description="<h2>Premium Whey Protein</h2><p>24g protein per serving.</p>",
        type="Sports Nutrition",
        vendor="Optimum Nutrition",
        tags=["protein powder", "whey protein", "post-workout"],
        lead_option="Size",
        variants=[variant1, variant2]
    )


@pytest.fixture
def draft_product_with_two_options():
    """Fixture for a draft product with two options (Size and Flavour)."""
    variant1 = Variant(
        option1_value=Option(option_name="Size", option_value="1kg"),
        option2_value=Option(option_name="Flavour", option_value="Strawberry"),
        sku=235052,
        barcode=9238957523,
        price=64.95,
        compare_at=79.95,
        product_weight=1.0,
        inventory_at_stores=InventoryAtStores(city=45, south_melbourne=28)
    )
    variant2 = Variant(
        option1_value=Option(option_name="Size", option_value="2kg"),
        option2_value=Option(option_name="Flavour", option_value="Strawberry"),
        sku=235053,
        barcode=9233952523,
        price=119.95,
        compare_at=149.95,
        product_weight=2.0,
        inventory_at_stores=InventoryAtStores(city=45, south_melbourne=28)
    )

    return DraftProduct(
        title="Gold Standard 100% Whey Protein",
        description="<h2>Premium Whey Protein</h2><p>High quality protein powder.</p>",
        type="Sports Nutrition",
        vendor="Optimum Nutrition",
        tags=["protein", "whey", "post-workout"],
        lead_option="Size",
        baby_options=["Flavour"],
        variants=[variant1, variant2]
    )


@pytest.fixture
def sample_inventory_request():
    """Fixture for a sample inventory update request."""
    return Inventory(
        inventory_item_id="44793372835937",
        stores=[
            Inputs(name_of_store="City", inventory_number=50),
            Inputs(name_of_store="South Melbourne", inventory_number=50)
        ]
    )


# -----------------------------------------------------------------------------
# Unit Tests
# -----------------------------------------------------------------------------

class TestMockShopClient:
    """Unit tests for MockShop client."""

    def test_make_a_product_draft_returns_response(
        self, mock_shop, draft_product_with_one_option
    ):
        """Test that make_a_product_draft returns a DraftResponse."""
        shop_name = os.getenv("SHOP_NAME", "test-shop")

        result = mock_shop.make_a_product_draft(
            shop_name=shop_name,
            product_listing=draft_product_with_one_option
        )

        assert result is not None
        assert isinstance(result, DraftResponse)

    def test_make_a_product_draft_returns_correct_title(
        self, mock_shop, draft_product_with_one_option
    ):
        """Test that DraftResponse has the correct title."""
        shop_name = os.getenv("SHOP_NAME", "test-shop")

        result = mock_shop.make_a_product_draft(
            shop_name=shop_name,
            product_listing=draft_product_with_one_option
        )

        assert result.title == draft_product_with_one_option.title

    def test_get_products_from_store(self, mock_shop):
        products = mock_shop.get_products_from_store()
        assert products

        print("Length Of Products: ", len(products))
        print(products)

    @pytest.mark.asyncio
    async def test_search_by_sku(self, mock_shop):
        sku =201
        sku_response = await mock_shop.search_by_sku(sku=sku)
        assert sku_response is None

        sku = 199
        sku_response = await mock_shop.search_by_sku(sku=sku)
        assert sku_response
        assert sku_response.sku == str(sku)

class TestDraftProductValidation:
    """Tests for DraftProduct model validation."""

    def test_validate_length_succeeds_for_valid_product(
        self, draft_product_with_two_options
    ):
        """Test that validate_length succeeds for a valid product."""
        # Should not raise an exception
        draft_product_with_two_options.validate_length()

    def test_options_are_correctly_extracted(self, draft_product_with_two_options):
        """Test that options are correctly extracted from variants."""
        draft_product_with_two_options.validate_length()
        options = draft_product_with_two_options.options

        assert options is not None
        assert len(options) == 2

        # Check option names are present
        option_names = [opt["name"] for opt in options]
        assert "Size" in option_names
        assert "Flavour" in option_names

    def test_options_contain_correct_values(self, draft_product_with_two_options):
        """Test that options contain the correct values."""
        draft_product_with_two_options.validate_length()
        options = draft_product_with_two_options.options

        # Find Size option and check values
        size_option = next(opt for opt in options if opt["name"] == "Size")
        assert "1kg" in size_option["values"]
        assert "2kg" in size_option["values"]


# -----------------------------------------------------------------------------
# Integration Tests
# -----------------------------------------------------------------------------

@pytest.mark.integration
class TestShopifyClientIntegration:
    """Integration tests using real Shopify API.

    These tests require Shopify credentials to be set:
    - SHOPIFY_API_KEY
    - SHOPIFY_API_SECRET
    - SHOPIFY_TOKEN
    - SHOP_NAME
    - SHOP_URL
    - LOCATION_ONE_ID
    - LOCATION_TWO_ID

    Run with: pytest -m integration
    """

    @pytest.fixture
    def real_client(self):
        """Create a real Shopify client."""
        load_dotenv()

        api_key = os.getenv("SHOPIFY_API_KEY")
        api_secret = os.getenv("SHOPIFY_API_SECRET")
        token = os.getenv("SHOPIFY_TOKEN")
        shop_name = os.getenv("SHOP_NAME")
        shop_url = os.getenv("SHOP_URL")
        location_one_id = f"gid://shopify/Location/{os.getenv('LOCATION_ONE_ID')}"
        location_two_id = f"gid://shopify/Location/{os.getenv('LOCATION_TWO_ID')}"

        locations = Locations(locations=[
            Location(name="City", id=location_one_id),
            Location(name="South Melbourne", id=location_two_id)
        ])

        return ShopifyClient(
            api_key=api_key,
            api_secret=api_secret,
            token=token,
            shop_url=shop_url,
            shop_name=shop_name,
            locations=locations
        )

    def test_get_products_from_store(self, real_client):
        """Test fetching products from the store."""
        result = real_client.get_products_from_store()

        assert result is not None
        assert isinstance(result, list)
        assert len(result) > 0

        print("Type: ", type(result[0]))

    def test_make_a_product_draft(self, real_client, draft_product_with_two_options):
        """Test creating a draft product."""
        result = real_client.make_a_product_draft(
            product_listing=draft_product_with_two_options
        )

        assert result is not None
        assert result.status_code == 200

    @pytest.mark.asyncio
    async def test_search_by_sku_success(self, real_client):
        """Test searching for a product via the sku"""
        sku = "130295"
        search_result = await real_client.search_by_sku(sku=sku)
        assert search_result is not None
        assert search_result.sku == sku
        print("Type: ", type(search_result))
        print("Result: ", search_result)

    @pytest.mark.asyncio
    async def test_search_by_sku_none(self, real_client):
        """Return a sku that doesnt yet exist in the shop"""
        search_result = await real_client.search_by_sku(sku="3253425626")
        assert search_result is None

    def test_fill_inventory(self, real_client, sample_inventory_request):
        """Test updating inventory levels."""
        result = real_client.fill_inventory(
            inventory_data=sample_inventory_request
        )

        assert result is True
