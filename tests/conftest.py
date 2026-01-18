"""
Shared pytest fixtures for the Product Generating Agent test suite.

This module provides:
- Mock fixtures for all external services (Shop, Scraper, VectorDb, Embeddor, LLM)
- Sample test data fixtures (products, variants, embeddings)
- Standardized TestCase pattern for input/expected result pairing
- pytest configuration (markers, logging)
"""
import pytest
from typing import Any, TypeVar, Generic
from pydantic import BaseModel

from qdrant_client.models import PointStruct, ScoredPoint

from product_agent.config import build_mock_service_container, build_service_container

from tests.mocks.shopify_mock import MockShop
from tests.mocks.firecrawl_mock import MockScraperClient
from tests.mocks.vector_db_mock import MockVectorDb
from tests.mocks.embeddings_mock import MockEmbeddor
from tests.mocks.llm_mock import MockLLM
from product_agent.infrastructure.shopify.schemas import (
    DraftProduct, DraftResponse, Variant, Option, InventoryAtStores
)
from product_agent.infrastructure.llm.prompts import PromptVariant
from product_agent.infrastructure.firecrawl.schemas import FireResult
from product_agent.models.query import QueryResponse
from product_agent.services.schemas import ProductExists


# -----------------------------------------------------------------------------
# Standardized Test Case Pattern
# -----------------------------------------------------------------------------

T = TypeVar("T")

class TestCase(BaseModel, Generic[T]):
    """
    Standardized test case structure for all tests.

    Usage:
        test_case = TestCase(
            data={"request_id": "123", "query": prompt_variant},
            expected={"type": QueryResponse, "field": "value"}
        )

        result = function_under_test(**test_case.data)
        assert isinstance(result, test_case.expected["type"])
    """
    data: dict[str, Any]
    expected: dict[str, Any]
    description: str | None = None

    class Config:
        arbitrary_types_allowed = True


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers",
        "integration: marks tests as integration tests (deselect with '-m not integration')"
    )

# -----------------------------------------------------------------------------
# Service Mock Fixtures
# -----------------------------------------------------------------------------

@pytest.fixture
def mock_shop():
    """Fixture providing a mock Shopify client."""
    return MockShop()


@pytest.fixture
def mock_scraper():
    """Fixture providing a mock Firecrawl scraper client."""
    return MockScraperClient()


@pytest.fixture
def mock_vector_db():
    """Fixture providing a mock Qdrant vector database client."""
    return MockVectorDb()


@pytest.fixture
def mock_embeddor():
    """Fixture providing a mock OpenAI embeddings client."""
    return MockEmbeddor()


@pytest.fixture
def mock_llm():
    """Fixture providing a mock LLM client."""
    return MockLLM()

@pytest.fixture
def mock_service_container():
    """Fixture building a suite of mocked dependencies"""
    return build_mock_service_container()

@pytest.fixture
def service_container():
    """Fixture building a suite of dependencies"""
    return build_service_container()

# -----------------------------------------------------------------------------
# Sample Test Data Fixtures
# -----------------------------------------------------------------------------

@pytest.fixture
def sample_variant():
    """Fixture providing a sample product variant."""
    return Variant(
        option1_value=Option(option_name="Size", option_value="500g"),
        sku=235053,
        barcode=9233952523,
        price=29.99,
        compare_at=39.99,
        product_weight=0.5,
        inventory_at_stores=InventoryAtStores(city=10, south_melbourne=20)
    )


@pytest.fixture
def sample_draft_product(sample_variant):
    """Fixture providing a sample draft product."""
    return DraftProduct(
        title="Test Product Title",
        description="This is a test product description",
        type="Supplement",
        vendor="Test Vendor",
        tags=["test", "sample"],
        lead_option="Size",
        variants=[sample_variant]
    )


@pytest.fixture
def sample_draft_product_with_two_options():
    """Fixture providing a sample draft product with two option types."""
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
def sample_scored_points():
    """Fixture providing sample scored points from vector search."""
    return [
        ScoredPoint(
            id=0,
            score=95.0,
            payload={"id": "product_0", "title": "Test Product 0"},
            vector=[0.0] * 1536,
            version=0
        ),
        ScoredPoint(
            id=1,
            score=87.5,
            payload={"id": "product_1", "title": "Test Product 1"},
            vector=[0.0] * 1536,
            version=0
        ),
        ScoredPoint(
            id=2,
            score=75.0,
            payload={"id": "product_2", "title": "Test Product 2"},
            vector=[0.0] * 1536,
            version=0
        ),
    ]


@pytest.fixture
def sample_embedding():
    """Fixture providing a sample 1536-dimension embedding vector."""
    return [0.1] * 1536


@pytest.fixture
def sample_point_struct():
    """Fixture providing a sample PointStruct for vector DB operations."""
    return PointStruct(
        id=1,
        vector=[0.1] * 1536,
        payload={"id": "test_product", "title": "Test Product"}
    )


# -----------------------------------------------------------------------------
# Test Document Fixtures
# -----------------------------------------------------------------------------

@pytest.fixture
def sample_documents_for_embedding():
    """Fixture providing sample documents for embedding tests."""
    return [
        "Optimum Nutrition Gold Standard Whey Protein",
        "C4 Original Pre-Workout Powder",
        "Nordic Naturals Ultimate Omega Fish Oil"
    ]


@pytest.fixture
def sample_shopify_product_data():
    """Fixture providing sample Shopify product data."""
    return [
        {
            "id": 6776951308385,
            "title": "Optimum Nutrition Gold Standard 100% Whey Protein",
            "body_html": "<h2>Premium Whey Protein</h2><p>24g protein per serving.</p>",
            "product_type": "Sports Nutrition",
            "tags": "protein powder, whey protein, post-workout",
            "vendor": "Optimum Nutrition"
        },
        {
            "id": 6776951308386,
            "title": "C4 Original Pre-Workout Powder",
            "body_html": "<h2>Explosive Energy</h2><p>150mg caffeine for energy.</p>",
            "product_type": "Pre-Workout",
            "tags": "pre-workout, energy, caffeine",
            "vendor": "Cellucor"
        },
    ]


# -----------------------------------------------------------------------------
# PromptVariant Fixtures
# -----------------------------------------------------------------------------

@pytest.fixture
def sample_prompt_variant():
    """Fixture providing a sample PromptVariant for workflow testing."""
    return PromptVariant(
        brand_name="EHP Labs",
        product_name="Oxyshred Protein Bar",
        variants=[
            Variant(
                option1_value=Option(option_name="Size", option_value="50g"),
                option2_value=Option(option_name="Flavour", option_value="White Choc Caramel"),
                sku=922026,
                barcode="0810095637971",
                price=4.95,
                product_weight=0.05,
                inventory_at_stores=InventoryAtStores(city=15, south_melbourne=15)
            ),
        ]
    )


# -----------------------------------------------------------------------------
# Standardized Test Cases (data + expected)
# -----------------------------------------------------------------------------

@pytest.fixture
def tc_query_extract():
    """
    Test case for query_extract service function.
    Tests that the LLM reformulates a product search query.
    """
    return TestCase(
        description="Query extraction should return title-cased brand and product",
        data={
            "query": PromptVariant(
                brand_name="ehp labs",
                product_name="oxyshred protein bar",
                variants=[
                    Variant(
                        option1_value=Option(option_name="Size", option_value="50g"),
                        sku=922026,
                        barcode="0810095637971",
                        price=4.95,
                        product_weight=0.05,
                    ),
                ]
            )
        },
        expected={
            "type": QueryResponse,
            "brand_name_title_cased": "Ehp Labs",
            "product_name_title_cased": "Oxyshred Protein Bar",
        }
    )


@pytest.fixture
def tc_check_product_exists_found_by_sku():
    """
    Test case for check_if_product_already_exists when product IS found via SKU.
    """
    return TestCase(
        description="Should return ProductExists when SKU matches existing product",
        data={
            "query": PromptVariant(
                brand_name="Optimum Nutrition",
                product_name="Gold Standard Whey",
                variants=[
                    Variant(
                        option1_value=Option(option_name="Size", option_value="2kg"),
                        sku=130295, # in mock anything over 200 signifies we dont have it, this is mock logic for this codebase
                        barcode="1234567890",
                        price=89.95,
                        product_weight=2.0,
                    ),
                ]
            )
        },
        expected={
            "type": ProductExists,
            "method": "shopify",
            "product_exists": True,
            "product": "Sanum Alkala N"
        }
    )


@pytest.fixture
def tc_check_product_exists_found_by_vector():
    """
    Test case for check_if_product_already_exists when product IS found via vector search.
    """
    return TestCase(
        description="Should return ProductExists when vector similarity exceeds threshold",
        data={
            "query": PromptVariant(
                brand_name="Optimum Nutrition",
                product_name="Gold Standard Whey",
                variants=[
                    Variant(
                        option1_value=Option(option_name="Size", option_value="2kg"),
                        sku=999999,  # SKU that won't match
                        barcode="0000000000",
                        price=89.95,
                        product_weight=2.0,
                    ),
                ]
            )
        },
        expected={
            "type": ProductExists,
            "method": "vector_search",
            "product_exists": True,
            "min_score": 0.92,
        }
    )


@pytest.fixture
def tc_check_product_exists_not_found():
    """
    Test case for check_if_product_already_exists when product does NOT exist.
    """
    return TestCase(
        description="Should return None when product not found by any method",
        data={
            "query": PromptVariant(
                brand_name="",
                product_name="Under 15 Char", # Helps the mock embedding, return a not found result from the DB
                variants=[
                    Variant(
                        option1_value=Option(option_name="Size", option_value="100g"),
                        sku=5123453, # Over 200 sku number, this is  mock logic to test both scenarios
                        barcode="0000000000",
                        price=19.95,
                        product_weight=0.1,
                    ),
                ]
            )
        },
        expected={
            "type": None,
            "product_exists": False,
        }
    )


@pytest.fixture
def tc_similarity_search():
    """
    Test case for similarity_search_svc function.
    """
    return TestCase(
        description="Should return scored points from vector database",
        data={
            "vector_query": [0.1] * 1536,
            "results_wanted": 5,
        },
        expected={
            "min_results": 1,
            "max_results": 5,
            "has_score": True,
            "has_payload": True,
        }
    )


@pytest.fixture
def tc_markdown_summariser():
    """
    Test case for markdown_summariser function.
    """
    return TestCase(
        description="Should summarise markdown content for product",
        data={
            "title": "Premium Whey Protein",
            "markdown": """
            # Premium Whey Protein

            ## Overview
            High quality protein powder with 24g protein per serving.

            ## Benefits
            - Muscle recovery
            - Great taste
            - Easy mixing
            """,
        },
        expected={
            "type": str,
            "min_length": 10,
            "is_not_empty": True,
        }
    )


@pytest.fixture
def tc_query_synthesis_low_relevance():
    """
    Test case for query_synthesis when similar products have LOW relevance.

    Scenario: User searches for pre-workout, but vector DB returned protein products.
    Expected: Agent should detect mismatch and trigger requery.
    """
    # Similar products that DON'T match the target category (wrong category)
    wrong_similar_products = [
        PointStruct(
            id="6776123456789",
            vector=[0.1] * 1536,
            payload={
                "title": "Optimum Nutrition Gold Standard 100% Whey",
                "body_html": "<h2>24g Protein per Serving</h2>",
                "product_type": "Whey Protein",
                "tags": "Protein Powder, Whey, Sports Nutrition",
                "vendor": "Optimum Nutrition"
            }
        ),
        PointStruct(
            id="6776987654321",
            vector=[0.1] * 1536,
            payload={
                "title": "Dymatize ISO100 Hydrolyzed Protein",
                "body_html": "<h2>Fast Absorbing Protein</h2>",
                "product_type": "Whey Protein Isolate",
                "tags": "Protein, Isolate, Post-Workout",
                "vendor": "Dymatize"
            }
        ),
        PointStruct(
            id="6776555444333",
            vector=[0.1] * 1536,
            payload={
                "title": "MuscleTech Mass Gainer",
                "body_html": "<h2>1000 Calories Per Serving</h2>",
                "product_type": "Mass Gainer",
                "tags": "Weight Gain, Mass Gainer, Bulking",
                "vendor": "MuscleTech"
            }
        ),
    ]

    return TestCase(
        description="Should detect low relevance and requery for pre-workout products",
        data={
            "query": "Cellucor C4 Original Pre-Workout",
            "similar_products": wrong_similar_products,
        },
        expected={
            "relevance_below": 50,
            "action_taken": "requery",
            "has_similar_products": True,
        }
    )


@pytest.fixture
def tc_query_synthesis_high_relevance():
    """
    Test case for query_synthesis when similar products have HIGH relevance.

    Scenario: User searches for protein, vector DB returned protein products.
    Expected: Agent should accept results without requery.
    """
    # Similar products that MATCH the target category
    matching_similar_products = [
        PointStruct(
            id="6776123456789",
            vector=[0.1] * 1536,
            payload={
                "title": "Optimum Nutrition Gold Standard 100% Whey",
                "body_html": "<h2>24g Protein per Serving</h2>",
                "product_type": "Whey Protein",
                "tags": "Protein Powder, Whey, Sports Nutrition",
                "vendor": "Optimum Nutrition"
            }
        ),
        PointStruct(
            id="6776987654321",
            vector=[0.1] * 1536,
            payload={
                "title": "Dymatize ISO100 Hydrolyzed Protein",
                "body_html": "<h2>Fast Absorbing Protein</h2>",
                "product_type": "Whey Protein Isolate",
                "tags": "Protein, Isolate, Post-Workout",
                "vendor": "Dymatize"
            }
        ),
        PointStruct(
            id="6776555444333",
            vector=[0.1] * 1536,
            payload={
                "title": "BSN Syntha-6 Protein Powder",
                "body_html": "<h2>Multi-Phase Protein Release</h2>",
                "product_type": "Protein Blend",
                "tags": "Protein, Blend, Recovery",
                "vendor": "BSN"
            }
        ),
    ]

    return TestCase(
        description="Should accept high relevance results without requery",
        data={
            "query": "EHP Labs Oxyshred Lean Protein",
            "similar_products": matching_similar_products,
        },
        expected={
            "relevance_above": 50,
            "action_taken": "use_current",
            "has_similar_products": True,
        }
    )
