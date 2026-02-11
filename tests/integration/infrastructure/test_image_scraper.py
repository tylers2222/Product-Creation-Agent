import pytest

@pytest.mark.integration
class TestImageScraper:
    """
    Testing the image scraper / grabber
    """
    @pytest.mark.asyncio
    async def test_get_images(self, real_service_container):
        """
        Test getting image list from google
        """
        product = "Dr. Bronner's - Pure Castile Liquid Soap 946 ml - Organic Oils - 18-in-1 Multi-functional Soap Unscented "
        optimised_for_search = "Buy Online Australia"

        query = product + optimised_for_search
        print("Query: ", query)

        image_list = await real_service_container.image_scraper.get_google_images(
            query=query,
            num_images=5,
            headless=True
        )

        assert image_list is not None
        assert isinstance(image_list,s list)

        print("\nList: ", image_list)