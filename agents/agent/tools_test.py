"""
Tests for agent tools and service functions.

Unit tests use mock dependencies, integration tests use real services.
"""
import pytest
from qdrant_client.models import PointStruct

from services.misc import search_products_comprehensive
from agents.infrastructure.firecrawl_api.schema import FireResult


# -----------------------------------------------------------------------------
# Unit Tests
# -----------------------------------------------------------------------------

class TestMockDependencies:
    """Unit tests to verify mock dependencies work correctly."""

    def test_scraper_returns_fire_result(self, mock_scraper):
        """Test that mock scraper returns a FireResult object."""
        query = "Caruso's Ashwagandha + Sleep"

        fire_result = mock_scraper.scrape_and_search_site(query=query)

        assert fire_result is not None
        assert isinstance(fire_result, FireResult)
        assert fire_result.data is not None

    def test_embeddor_returns_embeddings(self, mock_embeddor):
        """Test that mock embeddor returns embedding vectors."""
        query = "Caruso's Ashwagandha + Sleep"

        embeddings = mock_embeddor.embed_documents([query])

        assert embeddings is not None
        assert len(embeddings) == 1
        assert isinstance(embeddings[0], list)

    def test_vector_db_upsert_and_search(self, mock_vector_db, mock_embeddor):
        """Test that mock vector DB can upsert and search points."""
        query = "Test product"
        embeddings = mock_embeddor.embed_documents([query])

        # Upsert a point
        point = PointStruct(id=1, vector=[0.1], payload={"id": 1})
        db_response = mock_vector_db.upsert_points("test_collection", points=[point])

        assert db_response is not None

        # Search for points
        points = mock_vector_db.search_points("test_collection", embeddings[0], k=2)

        assert points is not None
        assert len(points) > 0


# -----------------------------------------------------------------------------
# Integration Tests
# -----------------------------------------------------------------------------

@pytest.mark.integration
class TestSearchProductsComprehensiveIntegration:
    """Integration tests using real external services.

    These tests require:
    - FIRECRAWL_API_KEY for web scraping
    - QDRANT_URL, QDRANT_API_KEY for vector database
    - OPENAI_API_KEY for embeddings and LLM

    Run with: pytest -m integration
    """

    @pytest.fixture
    def real_scraper(self):
        """Create a real Firecrawl client."""
        from agents.infrastructure.firecrawl_api.client import FirecrawlClient
        import os
        from dotenv import load_dotenv

        load_dotenv()
        return FirecrawlClient(api_key=os.getenv("FIRECRAWL_API_KEY"))

    @pytest.fixture
    def real_embeddor(self):
        """Create a real OpenAI embeddings client."""
        from agents.infrastructure.vector_database.embeddings import Embeddings
        return Embeddings()

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
    def real_llm(self):
        """Create a real LLM client."""
        from agents.agent.llm import llm_client
        return llm_client()

    def test_search_products_comprehensive(
        self, real_scraper, real_embeddor, real_vector_db, real_llm
    ):
        """Test search_products_comprehensive with real services."""
        query = "Optimum Nutrition Whey Protein"

        scraper_result, vector_result = search_products_comprehensive(
            query=query,
            scraper=real_scraper,
            embeddor=real_embeddor,
            vector_db=real_vector_db,
            llm=real_llm
        )

        assert scraper_result is not None
        assert vector_result is not None
