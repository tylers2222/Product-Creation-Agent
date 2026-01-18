"""
Tests for Firecrawl scraper client.

Unit tests use mock client, integration tests use real Firecrawl API.
"""
import os
from dotenv import load_dotenv
import pytest
from firecrawl.types import SearchData, SearchResultWeb
from product_agent.infrastructure.firecrawl.client import FirecrawlClient
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
        print()
        for idx, res in enumerate(result.data.web):
            if not res.markdown:
                continue
            print()
            print()
            print(f"Markdown {idx}")
            print("Type: ", type(res.markdown))
            markdown_no_newlines = res.markdown.replace("\n", "")
            print(markdown_no_newlines)
            print("Length Of Markdown: ", len(markdown_no_newlines))

        for idx, res in enumerate(result.data.web):
            if not res.markdown:
                continue
            print()
            print()
            print(f"Markdown {idx}")
            markdown_no_newlines = res.markdown.replace("\n", "")
            print("Length Of Markdown: ", len(markdown_no_newlines))

    def test_getting_urls(self, real_scraper):
        """Test getting multiple urls data"""
        query = "Optimum Nutrition Gold Standard 100% Whey buy online"
        urls = real_scraper.get_urls_for_query(query=query)
        print(urls)

    def test_extracting_url(self, real_scraper):
        """Test using the smart extract feature by FireCrawl"""
        url = "https://www.optimumnutrition.com/en-au/products/gold-standard-100-whey-protein-powder-au"
        prompt = """
        Extract the products:
        - Title
        - Description
        - Any data such as additional info, benefits, ingredients
        - If a dropdown has data about the product get that information

        Dont get:
        - Reviews 
        - Any data that doesnt describe the product
        """

        data = real_scraper.extract_from_url(url=url, prompt=prompt)
        print(data.model_dump_json(indent=3))

    def test_extracting_urls(self, real_scraper):
        """Test using the smart extract feature by FireCrawl with multiple URLs"""
        url_1 = "https://www.optimumnutrition.com/en-au/products/gold-standard-100-whey-protein-powder-au"
        url_2 = "https://www.nutritionwarehouse.com.au/products/gold-standard-100-whey-by-optimum-nutrition?variant=42556493856995"

        # Create SearchData with SearchResultWeb objects
        web_results = [
            SearchResultWeb(url=url_1),
            SearchResultWeb(url=url_2)
        ]
        search_data = SearchData(web=web_results)
        
        data = real_scraper.extract_from_urls(url_data=search_data)
        print(data.model_dump_json(indent=3))