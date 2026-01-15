"""
Tests for Firecrawl scraper client.

Unit tests use mock client, integration tests use real Firecrawl API.
"""
import pytest

from agents.infrastructure.firecrawl_api.schema import FireResult


# -----------------------------------------------------------------------------
# Unit Tests
# -----------------------------------------------------------------------------

class TestFirecrawlClient:
    """Unit tests for the Firecrawl scraper client."""

    def test_scrape_and_search_returns_fire_result(self, mock_scraper):
        """Test that scrape_and_search_site returns a FireResult."""
        result = mock_scraper.scrape_and_search_site(query="Test query")

        assert result is not None
        assert isinstance(result, FireResult)

    def test_fire_result_has_data(self, mock_scraper):
        """Test that FireResult contains data."""
        result = mock_scraper.scrape_and_search_site(query="Test query")

        assert result.data is not None

    def test_fire_result_has_query(self, mock_scraper):
        """Test that FireResult contains the query."""
        query = "Optimum Nutrition Whey"
        result = mock_scraper.scrape_and_search_site(query=query)

        assert result.query is not None

    def test_fire_result_data_has_web_results(self, mock_scraper):
        """Test that FireResult data contains web results."""
        result = mock_scraper.scrape_and_search_site(query="Test query")

        assert hasattr(result.data, 'web')
        assert result.data.web is not None
        assert len(result.data.web) > 0


# -----------------------------------------------------------------------------
# Integration Tests
# -----------------------------------------------------------------------------

@pytest.mark.integration
class TestFirecrawlClientIntegration:
    """Integration tests using real Firecrawl API.

    These tests require FIRECRAWL_API_KEY to be set.

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

    def test_real_scrape_returns_results(self, real_scraper):
        """Test that real scraping returns results."""
        query = "Optimum Nutrition Whey Protein"

        result = real_scraper.scrape_and_search_site(query=query, limit=3)

        assert result is not None
        assert isinstance(result, FireResult)
        assert result.data is not None

    def test_real_scrape_web_results_have_markdown(self, real_scraper):
        """Test that web results contain markdown content."""
        query = "Optimum Nutrition Whey Protein"

        result = real_scraper.scrape_and_search_site(query=query, limit=3)

        assert result.data.web is not None
        assert len(result.data.web) > 0

        # Check first result has markdown
        first_result = result.data.web[0]
        assert hasattr(first_result, 'markdown')
