import pytest
from unittest.mock import Mock

from product_agent.services.infrastructure.scraping import (
    scrape_results_svc,
    scraping_url_svc,
    batch_scraping_url_svc
)

class TestScrapingService:
    """Testing the scraper in the service layer"""
    def test_scrape_results_svc(self, search_strs, mock_service_container):
        """Test the scraper in service layer"""
        scrape_result = scrape_results_svc(search_str=search_strs[0], scraper=mock_service_container.scraper)
        assert scrape_result is not None
        assert len(scrape_result.result) > 0
        assert not scrape_result.all_failed

class TestScrapingUrlService:
    """Testing the scraping_url_svc function"""
    
    def test_scraping_url_with_empty_string_raises_value_error(self):
        """Test that empty string raises ValueError"""
        mock_scraper = Mock()
        
        with pytest.raises(ValueError, match="Url was empty"):
            scraping_url_svc(url="", scraper=mock_scraper)
    
    def test_scraping_url_with_none_raises_error(self):
        """Test that None raises TypeError"""
        mock_scraper = Mock()
        
        with pytest.raises(TypeError):
            scraping_url_svc(url=None, scraper=mock_scraper)

class TestBatchScrapingUrlService:
    """Testing the batch_scraping_url_svc function"""
    
    def test_batch_scraping_with_empty_list_raises_value_error(self):
        """Test that empty list raises ValueError"""
        mock_scraper = Mock()
        
        with pytest.raises(ValueError, match="No Urls recieved"):
            batch_scraping_url_svc(urls=[], scraper=mock_scraper)
    
    def test_batch_scraping_with_none_raises_error(self):
        """Test that None raises TypeError"""
        mock_scraper = Mock()
        
        with pytest.raises(TypeError):
            batch_scraping_url_svc(urls=None, scraper=mock_scraper)
