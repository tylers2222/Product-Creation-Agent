import pytest
from unittest.mock import patch
from product_agent.services.infrastructure.image_scraper import image_scraper_svc, image_to_bytes_svc

class TestImageScraper:
    """Testing business logic in the image scraper service layer"""
    @pytest.mark.asyncio
    async def test_image_scraper_svc(
        self,
        interally_mocked_service_container
    ):
        """Testing obtaining images from a network request in the svc layer"""

        image_url_list= await image_scraper_svc(
            image_scraper=interally_mocked_service_container.image_scraper,
            query="Mock Query",
        )

        assert image_url_list is not None
        assert isinstance(image_url_list, list)

    @pytest.mark.asyncio
    @patch("product_agent.services.infrastructure.image_scraper.get_bytes")
    async def test_image_to_bytes(
        self,
        get_bytes_func,
        interally_mocked_service_container
    ):
        """Testing getting the image bytes from a url in the svc layer"""
        get_bytes_func.side_effect = [
            "a"*5,
            "b"*5,
            "c"*5,
            Exception("Failed to get bytes"),
            "e"*5,
        ]

        image_urls = await interally_mocked_service_container.image_scraper.get_google_images(
            query="Hi"
        )
        print("Type: ", type(image_urls))

        image_bytes = await image_to_bytes_svc(
            image_urls=image_urls
        )

        assert image_bytes is not None
        assert isinstance(image_bytes, dict)
        
        assert len(image_bytes) == 4