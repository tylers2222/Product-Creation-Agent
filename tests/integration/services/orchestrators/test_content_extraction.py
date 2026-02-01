import pytest

from product_agent.services.orchestrators.content_extraction import scrape_with_llm_svc

class TestContentExtraction:
    """
    Test the co-ordination of multiple services
    1) Scraper providing the markdowns
    2) LLM getting the product data
    """
    @pytest.mark.asyncio
    async def test_scrape_with_llm_svc(self, search_strs, real_service_container):
        """Testing the function scrape_with_llm_svc"""
        results = await scrape_with_llm_svc(search_strs[0], 
            real_service_container.scraper, 
            real_service_container.llm["gemini"],
            model="scraper_mini",
            limit_results=4
        )
        assert results is not None
        assert len(results) > 0

        for idx, result in enumerate(results):
            print(f"{idx}) ------------------------------------------------------")
            print(result.text)
            print()
            print("------------------------------------------------------")

    @pytest.mark.asyncio
    async def test_analyse_markdowns_with_llm_svc(self, ):
        """
        Test sending markdowns to LLM with system prompt
        In the logs check the cached tokens amount
        Remembering implicit and explicit cache
        """

        pass