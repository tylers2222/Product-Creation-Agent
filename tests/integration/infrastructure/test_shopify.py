"""
Integration tests for ShopifyClient.

These tests interact with the real Shopify API and require:
- Valid SHOPIFY_TOKEN environment variable
- Valid SHOP_NAME environment variable
- Valid LOCATION_ONE_ID and LOCATION_TWO_ID environment variables
"""
import pytest


@pytest.mark.integration
class TestShopifyClient:
    """Integration tests for ShopifyClient using real Shopify API."""

    @pytest.mark.asyncio
    async def test_search_by_sku_found(self, real_shopify_client):
        """Test searching for a product by SKU that exists in the store."""
        sku = 922094

        async with real_shopify_client as client:
            result = await client.search_by_sku(sku=sku)

        # Assert we got a result
        assert result is not None, f"Expected to find product with SKU {sku}"
        assert result.sku == str(sku), f"Expected SKU {sku}, got {result.sku}"
        assert result.product is not None, "Expected product to be present"
        assert result.product.title is not None, "Expected product title to be present"

        # Log result for debugging
        print(f"\n✅ Found product: {result.product.title}")
        print(f"   SKU: {result.sku}")

    @pytest.mark.asyncio
    async def test_search_by_sku_not_found(self, real_shopify_client):
        """Test searching for a product by SKU that doesn't exist."""
        sku = 9999999999  # Non-existent SKU

        async with real_shopify_client as client:
            result = await client.search_by_sku(sku=sku)

        # Assert we got None for non-existent product
        assert result is None, f"Expected None for non-existent SKU {sku}, got {result}"
        print(f"\n✅ Correctly returned None for non-existent SKU {sku}")
