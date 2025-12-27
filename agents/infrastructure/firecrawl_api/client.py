from firecrawl import Firecrawl
from pydantic import BaseModel
from dotenv import load_dotenv
from typing import Optional, Dict, Any, Protocol, runtime_checkable
from functools import wraps
import os
import time
import logging
from .exceptions import FirecrawlError
from .schema import FireResult, DataResult

os.chdir("..")
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

firecrawl_api_key = os.getenv("FIRECRAWL_API_KEY")
if not firecrawl_api_key:
    print("No Api Key")


class Scraper(Protocol):
    """An interface with scraping methods"""

    def scrape_and_search_site(self, query: str, limit: int = 5) -> FireResult:
        ...


class FirecrawlClient:
    def __init__(self, api_key: str):
        logger.info("Initialising Firecrawl Client...")
        self.client = Firecrawl(api_key=api_key)
        logger.info("Initialised Firecrawl Client Successful")

    def scrape_and_search_site(self, query: str, limit: int = 5):
        """Some filtering x business logic in the concrete due to the size of response, structured response helps LLM as well"""
        if limit > 10:
            raise ValueError("Limit on pages cant be greater than 10 due to cost principle")

        search = self.client.search(
            query = query,
            limit = limit,
            scrape_options = {
                "formats" :["markdown"],
                "onlyMainContent": True
            }
        )

        if not search:
            logger.info("No search results from scraper")
            raise FirecrawlError("No search returned")

        if not search.web:
            logger.info("successful search returned no url data")
            raise FirecrawlError("completed search returned no url data")

        return FireResult(
            data = search,
            query = query,
        )
