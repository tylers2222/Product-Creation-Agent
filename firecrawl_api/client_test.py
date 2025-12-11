import os
import sys
from dotenv import load_dotenv

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

os.chdir("..")
load_dotenv()

from firecrawl_api.client import FirecrawlClient, Scraper, FireResult
import json
from typing import Optional
import pytest
from collections import namedtuple
from langchain_core.documents import Document

firecrawl_client = FirecrawlClient()
query1 = "Rapid supplements cream of rice 1.2kg"

# Mock SearchData - mimics firecrawl's SearchData structure with a .web attribute
MockSearchData = namedtuple('SearchData', ['web'])

mock_search_data = MockSearchData(web=[
    Document(
        page_content="![Nutrition Warehouse logo](https://www.nutritionw",
        metadata={
            "title": "100% Pure Cream of Rice by Rapid Supplements - Nutrition Warehouse",
            "description": "Enjoy a nutritious and hearty bowl of goodness full of complex carbohydrates with 100% Cream of Rice By Rapid Supplements. This hearty meal supplement delivers a sustained energy supply to fuel your workouts. With 30 grams of carbohydrates per serving, you'll fuel your muscles with the proper nutrients. Order now!",
            "url": "https://www.nutritionwarehouse.com.au/products/100-pure-cream-of-rice-by-rapid-supplements?variant=42569760702691"
        }
    ),
    Document(
        page_content="[Skip to content](https://supplementsupply.com.au/",
        metadata={
            "title": "Rapid Supplement's – Cream of Rice – Supplement Supply",
            "description": None,
            "url": "https://supplementsupply.com.au/product/rapid-supplements-cream-of-rice/"
        }
    ),
    Document(
        page_content="[Skip to content](https://rapidsupps.com.au/produc",
        metadata={
            "title": "Cream Of Rice 30 Serves\n  \n  \n   – Rapid Supplements",
            "description": "Pure Cream of Rice is a delicious bowl of hearty goodness full of complex carbohydrates to fuel your workouts. Cream of rice can also be consumed as a healthy meal for a sustained energy supply. Naturally flavoured with no artificial sweeteners it is gentle on the stomach, ready in minutes and keeps you feeling fuller ",
            "url": "https://rapidsupps.com.au/products/cream-of-rice"
        }
    ),
    Document(
        page_content="[BLACK FRIDAY - UP TO 30% OFF SITEWIDE](https://ww",
        metadata={
            "title": " 100% Pure Cream of Rice by Rapid Supplements  \n     – Supplement Warehouse \n",
            "description": "100% Pure Cream of Rice by Rapid Supplements is a delicious nutritious bowl of hearty goodness full of complex carbohydrates to fuel your workouts alternatively Cream of Rice can be consumed as a hearty meal for a sustained energy supply. Order now!",
            "url": "https://www.supplementwarehouse.com.au/products/100-pure-cream-of-rice-by-rapid-supplements"
        }
    )
])

class MockScraperClient:
    def __init__(self):
        pass

    def scrape_and_search_site(self, query: str, limit: int = 5) -> FireResult:
        return FireResult(
            data=mock_search_data,
            query="Rapid supplements cream of rice 1.2kg"
        )

class UnitTests:
    def __init__(self):
        self.client: Optional[Scraper] = MockScraperClient()

    def test_scrape_and_search_site(self):
        fire_result = self.client.scrape_and_search_site()
        assert(type(fire_result) == FireResult)



def send_to_file():
    print("="*60)
    print("STARTING INTEGRATION TEST IN SCRAPER PACKAGE\n\n")

    fire_result = firecrawl_client.scrape_and_search_site(query1)
    assert(fire_result is not None)

    print(f"Type Of 'fire_result': {type(fire_result)}")
    print(f"Type Of 'fire_result.data': {type(fire_result.data)}")
    print(f"Type Of 'fire_result.data.web': {type(fire_result.data.web)}")
    print(f"Len Of Web List: {len(fire_result.data.web)}")
    print(f"Type Of First Item: {fire_result.data.web[0]}")
    print(f"First item has these attributes: {dir(fire_result.data.web[0])}")
    print(f"Does it have .markdown? {hasattr(fire_result.data.web[0], 'markdown')}")
    print(f"Does it have .get()? {hasattr(fire_result.data.web[0], 'get')}")

    os.makedirs("firecrawl_api/json_responses", exist_ok=True)
    with open("firecrawl_api/json_responses/search_and_scrape.json", "w") as f:
        num_of_chars_returned = f.write(fire_result.model_dump_json(indent=3))
        if num_of_chars_returned == 0:
            print("Failed to write to file")
        else:
            print("Wrote to file successfully")



    #print("Successfully written to file")

    #print("="*60)
    #print("RESULTS ARE IN...")
    #print(f"Success: {res.success}")
    #print(f"Query: {res.query}")
    #print(f"Estimate Tokens On Markdown: {res.token_count}")

    #for site in res.data:
    #    print()
    #    print(f"Title: {site.title}")
    #    print(f"Description: {site.description}")
    #    print(f"Url: {site.url}")
    #    print()

    #print("="*60)

if __name__ == "__main__":
    send_to_file()