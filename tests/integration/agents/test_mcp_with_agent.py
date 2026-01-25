import pytest
from ...conftest import scraper_agent_with_mcp

@pytest.mark.integration
class TestAgentResponse:
    """Test Class with Agents and their MCP tools"""
    @pytest.mark.asyncio
    async def test_agent_with_mcp(self, scraper_agent_with_mcp):
        """
        Test scraping agent using Playwright MCP

        Opinion: Terrible, meant for single small read tasks
        """
        query = """
        Can you search https://www.nutritionwarehouse.com.au/products/gold-standard-100-whey-by-optimum-nutrition?variant=42415330459875 
        and find the product title, description, price, data in dropdowns relating to the product such as directions or ingredients, any image urls related to the product only not suggested products. 
        Open the page once and get search for the data in one open
        
        Return in json format
        """
        response = await scraper_agent_with_mcp.ainvoke({"input": query})
        assert response is not None
        print("Type: ", type(response))
        print("Response: ", response)

    @pytest.mark.asyncio
    async def test_in_house_scraper(self):
        """
        Test firecrawl and gemini flash scraping markdown and getting a result
        """

        