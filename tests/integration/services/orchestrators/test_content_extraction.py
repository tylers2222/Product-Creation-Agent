import json
from pydantic import BaseModel
import pytest

from product_agent.services.orchestrators.content_extraction import analyse_markdowns_with_llm_svc, scrape_with_llm_svc

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
            print(result.model_dump_json(indent=3))
            print()
            print("------------------------------------------------------")

    @pytest.mark.asyncio
    async def test_analyse_markdowns_with_llm_svc(self, real_gemini_llm):
        """
        Test sending markdowns to LLM with system prompt
        In the logs check the cached tokens amount
        Remembering implicit and explicit cache
        """

        with open("tests/data/test_markdowns.json", encoding="utf-8") as markdown:
            markdown_data = json.load(markdown)["markdown"]

        llm_results = await analyse_markdowns_with_llm_svc(markdowns=[markdown_data],
            llm=real_gemini_llm,
            model="gemini-2.5-flash")

        assert llm_results is not None
        assert isinstance(llm_results, BaseModel)

        res_dict = llm_results.model_dump()
        for key, value in res_dict.items():
            print()
            print("Key: ", key)
            print("Value: ", value)