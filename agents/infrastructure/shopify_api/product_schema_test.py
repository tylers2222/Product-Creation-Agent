"""
Tests for Shopify product schema models.
"""
import pytest

from agents.infrastructure.shopify_api.product_schema import Fields


# -----------------------------------------------------------------------------
# Unit Tests
# -----------------------------------------------------------------------------

class TestFields:
    """Tests for the Fields model.

    Note: shopify_transform_fields() returns all fields that were explicitly set,
    regardless of whether they are True or False. It uses model_fields_set which
    tracks what fields were provided, not their values.
    """

    def test_shopify_transform_fields_returns_string(self):
        """Test that shopify_transform_fields returns a string."""
        fields = Fields(
            id=True,
            title=True,
            product_type=True,
            tags=True
        )

        result = fields.shopify_transform_fields()

        assert result is not None
        assert isinstance(result, str)

    def test_shopify_transform_fields_contains_set_fields(self):
        """Test that the result contains all set fields (regardless of value)."""
        fields = Fields(
            id=True,
            title=True,
            product_type=True,
            tags=True
        )

        result = fields.shopify_transform_fields()

        # Check each field is present (order may vary due to set iteration)
        assert "id" in result
        assert "title" in result
        assert "product_type" in result
        assert "tags" in result

    def test_shopify_transform_fields_correct_count(self):
        """Test that the correct number of fields is returned."""
        fields = Fields(
            id=True,
            title=True,
            product_type=True,
            tags=True
        )

        result = fields.shopify_transform_fields()

        # Split by comma and count
        field_list = [f.strip() for f in result.split(",")]
        assert len(field_list) == 4

    def test_shopify_transform_fields_with_fewer_fields(self):
        """Test with only 2 fields set."""
        fields = Fields(
            id=True,
            title=True
        )

        result = fields.shopify_transform_fields()

        assert "id" in result
        assert "title" in result
        # Unset fields should not be included
        assert "product_type" not in result
        assert "tags" not in result

    def test_shopify_transform_fields_with_no_fields_set(self):
        """Test behavior when no fields are explicitly set."""
        fields = Fields()

        result = fields.shopify_transform_fields()

        # Should return empty string when no fields are set
        assert result == "" or len(result.strip()) == 0
