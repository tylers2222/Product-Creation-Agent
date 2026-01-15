"""
Tests for Qdrant vector database client.

Unit tests use mock client, integration tests use real Qdrant instance.
"""
import pytest
from qdrant_client.models import PointStruct

from agents.infrastructure.vector_database.response_schema import DbResponse


# -----------------------------------------------------------------------------
# Test Data Fixtures
# -----------------------------------------------------------------------------

@pytest.fixture
def sample_points():
    """Fixture providing sample PointStruct objects for testing."""
    return [
        PointStruct(
            id=i,
            vector=[0.1 * i] * 1536,
            payload={"id": f"product_{i}", "title": f"Product {i}"}
        )
        for i in range(5)
    ]


@pytest.fixture
def sample_product_data():
    """Fixture providing sample product data for embedding tests."""
    return [
        {
            "product_name": "Optimum Nutrition Gold Standard 100% Whey Protein",
            "description": "Premium whey protein supplement",
            "product_type": "Sports Nutrition",
            "tags": ["protein", "whey", "post-workout"]
        },
        {
            "product_name": "Nature's Way Activated B-Complex",
            "description": "Complete B vitamin complex",
            "product_type": "Vitamins",
            "tags": ["vitamins", "B-complex", "energy"]
        },
        {
            "product_name": "Blackmores Omega Daily",
            "description": "Fish oil omega-3 supplement",
            "product_type": "Supplements",
            "tags": ["omega-3", "fish oil", "heart health"]
        },
    ]


# -----------------------------------------------------------------------------
# Unit Tests
# -----------------------------------------------------------------------------

class TestMockVectorDb:
    """Unit tests for MockVectorDb client."""

    def test_upsert_points_returns_response(self, mock_vector_db, sample_points):
        """Test that upsert_points returns a DbResponse."""
        result = mock_vector_db.upsert_points(
            collection_name="test_collection",
            points=sample_points
        )

        assert result is not None
        assert isinstance(result, DbResponse)

    def test_upsert_points_tracks_records(self, mock_vector_db, sample_points):
        """Test that upsert tracks the number of records inserted."""
        result = mock_vector_db.upsert_points(
            collection_name="test_collection",
            points=sample_points
        )

        assert result.records_inserted == len(sample_points)

    def test_search_points_returns_list(self, mock_vector_db, sample_embedding):
        """Test that search_points returns a list of results."""
        result = mock_vector_db.search_points(
            collection_name="test_collection",
            query_vector=sample_embedding,
            k=5
        )

        assert result is not None
        assert isinstance(result, list)
        assert len(result) > 0

    def test_search_points_results_have_payload(self, mock_vector_db, sample_embedding):
        """Test that search results include payload data."""
        results = mock_vector_db.search_points(
            collection_name="test_collection",
            query_vector=sample_embedding,
            k=3
        )

        for result in results:
            assert hasattr(result, 'payload')
            assert result.payload is not None

    def test_search_points_results_have_score(self, mock_vector_db, sample_embedding):
        """Test that search results include similarity scores."""
        results = mock_vector_db.search_points(
            collection_name="test_collection",
            query_vector=sample_embedding,
            k=3
        )

        for result in results:
            assert hasattr(result, 'score')
            assert isinstance(result.score, (int, float))


# -----------------------------------------------------------------------------
# Integration Tests
# -----------------------------------------------------------------------------

@pytest.mark.integration
class TestVectorDatabaseIntegration:
    """Integration tests using real Qdrant instance.

    These tests require:
    - QDRANT_URL
    - QDRANT_API_KEY
    - OPENAI_API_KEY (for embeddings)

    Run with: pytest -m integration
    """

    @pytest.fixture
    def real_vector_db(self):
        """Create a real Qdrant vector database client."""
        from agents.infrastructure.vector_database.db import vector_database
        import os
        from dotenv import load_dotenv

        load_dotenv()
        return vector_database(
            os.getenv("QDRANT_URL"),
            os.getenv("QDRANT_API_KEY")
        )

    @pytest.fixture
    def real_embeddor(self):
        """Create a real OpenAI embeddings client."""
        from agents.infrastructure.vector_database.embeddings import Embeddings
        return Embeddings()

    def test_search_returns_results(self, real_vector_db, real_embeddor):
        """Test that search returns results from the database."""
        search_string = "Vitamin D3"
        embeddings = real_embeddor.embed_documents([search_string])

        results = real_vector_db.search_points(
            collection_name="shopify_products",
            query_vector=embeddings[0],
            k=5
        )

        assert results is not None
        assert isinstance(results, list)

    def test_search_results_have_titles(self, real_vector_db, real_embeddor):
        """Test that search results have product titles in payload."""
        search_string = "Protein powder"
        embeddings = real_embeddor.embed_documents([search_string])

        results = real_vector_db.search_points(
            collection_name="shopify_products",
            query_vector=embeddings[0],
            k=3
        )

        for result in results:
            assert result.payload is not None
            assert "title" in result.payload

    def test_upsert_points_succeeds(self, real_vector_db, sample_points):
        """Test that upserting points to the database succeeds."""
        result = real_vector_db.upsert_points(
            collection_name="shopify_products",
            points=sample_points
        )

        assert result is not None
        assert result.error is None
