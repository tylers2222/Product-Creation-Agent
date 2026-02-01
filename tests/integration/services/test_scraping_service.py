import pytest 

from product_agent.services.infrastructure.scraping import scrape_results_svc

class TestScrapingService:
    """Testing scrapers in the service layer"""
    @pytest.fixture
    def urls(self):
        return [
            "https://www.nutritionwarehouse.com.au/products/gold-standard-100-whey-by-optimum-nutrition?variant=42556493856995",
            "https://www.chemistwarehouse.com.au/buy/150484/optimum-nutrition-gold-standard-100-whey-vanilla-ice-cream-907g",

        ]
    def test_scrape_results_svc(self, real_service_container):
        """Test the scraper service obtaining the markdowns"""
        search_str = "Optimum Nutrition Gold Standard 100% Whey buy online"
        scraper_response = scrape_results_svc(search_str=search_str, scraper=real_service_container.scraper)
        assert scraper_response is not None
        assert not scraper_response.all_failed
        assert len(scraper_response.result) > 0

        print("Length Of Result: ", len(scraper_response.result))