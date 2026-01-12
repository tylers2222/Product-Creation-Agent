import os
import sys
from dotenv import load_dotenv
from typing import Optional
from collections import namedtuple

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

os.chdir("..")
load_dotenv()

from agents.infrastructure.firecrawl_api.client import FirecrawlClient, Scraper, FireResult
from agents.infrastructure.firecrawl_api.mock import MockScraperClient

class UnitTests:
    def __init__(self):
        self.client: Scraper = MockScraperClient()

    def test_scrape_and_search_site(self):
        fire_result = self.client.scrape_and_search_site()
        assert type(fire_result) == FireResult


def send_to_file():
    print("="*60)
    print("STARTING INTEGRATION TEST IN SCRAPER PACKAGE\n\n")
    firecrawl_client = FirecrawlClient(api_key=os.getenv("FIRECRAWL_API_KEY"))

    query1 = "Optimum Nutrition Whey afdsafsdf" #fix
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