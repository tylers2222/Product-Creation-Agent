import pytest
import os
import json
from dotenv import load_dotenv

from product_agent.infrastructure.firecrawl.client import KadoaScraper, FirecrawlClient
from product_agent.infrastructure.firecrawl.schemas import FireResult
from firecrawl.types import SearchData, SearchResultWeb

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

    def test_single_url_scrape(self, real_scraper):
        """
        Testing a single scraped url
        Turns a url into its markdown
        """
        url = "https://www.optimumnutrition.com/en-us/products/gold-standard-100-whey-protein-powder"
        response = real_scraper.scraper_url_to_markdown(url)
        assert response is not None
        print("Dir: ", dir(response))
        print()
        print("Type: ", type(response))
        print()
        print(response)

    def test_single_url_scrape_different_models(self):
        """ 
        Test multiple models in the same provider
        Found some models of gemini werent omitting what i wanted
        had a markdown, had somethings that werent being added
        Gemini 2.0 Flash was the original model
        """
        

    def test_batch_scrape(self, real_scraper):
        urls = [
            "https://www.evelynfaye.com.au/products/ehp-labs-acetyl-l-carnitine",
            "https://www.nutritionwarehouse.com.au/products/gold-standard-100-whey-by-optimum-nutrition?variant=42556493856995"
        ]

        response = real_scraper.batch_scraper_url_to_markdown(urls)
        assert response is not None
        print("Dir: ", dir(response))
        print()
        print("Type: ", type(response))
        print()
        for markdown in response:
            print("\n\n", markdown)

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
        assert urls is not None
        print("Dir: ", dir(urls))
        print()
        print("Type: ", type(urls))
        print()
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
        assert data is not None
        print(data.model_dump_json(indent=3))


@pytest.mark.integration
class TestKadoaScraper:
    """A test for Koadoas Ai scraper"""

    @pytest.fixture
    def real_scraper(self):
        """Returns a real instance of the scraper"""
        load_dotenv()
        return KadoaScraper(os.getenv("KADOA_API_KEY"))

    @pytest.fixture
    def urls(self):
        return [
            "https://www.optimumnutrition.com/en-au/products/gold-standard-100-whey-protein-powder-au",
            "https://www.nutritionwarehouse.com.au/products/gold-standard-100-whey-by-optimum-nutrition?variant=42556493856995"
        ]

    def test_single_url(self, real_scraper, urls):
        """Testing a single url from the Kadoa client"""
        url = urls[0]
        print("STARTING WITH URL: ", url)
        scrape_result = real_scraper.scrape_url(url=urls[0])
        assert scrape_result is not None

        print("Type: ", type(scrape_result))
        print()
        print("Dir: ", dir(scrape_result))
        print()
        print("Result: ", scrape_result.model_dump_json(indent=3))

    def test_single_url_http(self, real_scraper, urls):
        url = urls[0]
        print("STARTING WITH URL: ", url)

        response = real_scraper.scrape_url_http(url=url)
        print(json.dumps(response, indent=3))