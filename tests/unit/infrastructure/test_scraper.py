"""
Tests for Firecrawl scraper client.

Unit tests use mock client, integration tests use real Firecrawl API.
"""
from firecrawl.types import SearchData, SearchResultWeb
from product_agent.infrastructure.firecrawl.client import FirecrawlClient, KadoaScraper
from product_agent.infrastructure.firecrawl.schemas import FireResult

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

    def test_scraper_url_to_markdown_returns_dict(self, mock_scraper):
        """Test that scraper_url_to_markdown returns a dictionary with markdown."""
        url = "https://example.com/product"
        result = mock_scraper.scraper_url_to_markdown(url=url)

        assert result is not None
        assert isinstance(result, dict)

    def test_scraper_url_to_markdown_has_markdown_field(self, mock_scraper):
        """Test that result contains markdown field."""
        url = "https://example.com/product"
        result = mock_scraper.scraper_url_to_markdown(url=url)

        assert 'markdown' in result
        assert result['markdown'] is not None
        assert isinstance(result['markdown'], str)
        assert len(result['markdown']) > 0

    def test_scraper_url_to_markdown_has_metadata(self, mock_scraper):
        """Test that result contains metadata."""
        url = "https://example.com/product"
        result = mock_scraper.scraper_url_to_markdown(url=url)

        assert 'metadata' in result
        assert result['metadata'] is not None
        assert 'url' in result['metadata']
        assert result['metadata']['url'] == url

    def test_batch_scraper_url_to_markdown_returns_job(self, mock_scraper):
        """Test that batch_scraper_url_to_markdown returns a job object."""
        urls = [
            "https://example.com/product1",
            "https://example.com/product2",
            "https://example.com/product3"
        ]
        result = mock_scraper.batch_scraper_url_to_markdown(urls=urls)

        assert result is not None
        assert hasattr(result, 'id')
        assert hasattr(result, 'status')

    def test_batch_scraper_url_to_markdown_has_results(self, mock_scraper):
        """Test that batch job contains results."""
        urls = [
            "https://example.com/product1",
            "https://example.com/product2"
        ]
        job = mock_scraper.batch_scraper_url_to_markdown(urls=urls)

        assert hasattr(job, 'results')
        assert job.results is not None
        assert len(job.results) == len(urls)

    def test_batch_scraper_url_to_markdown_results_have_markdown(self, mock_scraper):
        """Test that each result in batch job has markdown content."""
        urls = [
            "https://example.com/product1",
            "https://example.com/product2"
        ]
        job = mock_scraper.batch_scraper_url_to_markdown(urls=urls)

        for result in job.results:
            assert 'markdown' in result
            assert result['markdown'] is not None
            assert isinstance(result['markdown'], str)
            assert len(result['markdown']) > 0

    def test_batch_scraper_url_to_markdown_empty_list(self, mock_scraper):
        """Test batch scraper with empty URL list."""
        urls = []
        job = mock_scraper.batch_scraper_url_to_markdown(urls=urls)

        assert job is not None
        assert hasattr(job, 'results')
        assert len(job.results) == 0

