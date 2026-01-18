import inspect
import re
from firecrawl import Firecrawl
from firecrawl.types import ScrapeOptions, ScrapeFormats, SearchData
from pydantic import BaseModel
from dotenv import load_dotenv
from typing import Optional, Dict, Any, Protocol, runtime_checkable
from functools import wraps
import os
import time
import structlog
from .exceptions import FirecrawlError
from .schemas import FireResult, DataResult

logger = structlog.get_logger(__name__)


def clean_markdown(markdown: str) -> str:
    """
    Remove junk from scraped markdown to reduce token costs.

    Removes:
    - Image references (![alt](url))
    - CDN URLs with query parameters
    - Navigation links (Skip to content, etc.)
    - Cart/UI text
    - Multiple consecutive newlines
    - Common UI button text

    This can reduce markdown size by 80-90%, saving significant LLM costs.
    """
    if not markdown:
        return ""

    original_length = len(markdown)

    # Remove image references (![alt](url))
    markdown = re.sub(r'!\[.*?\]\(.*?\)', '', markdown)

    # Remove standalone CDN URLs with query params (png, jpg, etc.)
    markdown = re.sub(r'https?://[^\s)]+\.(png|jpg|jpeg|gif|webp)[^\s)]*', '', markdown)

    # Remove URLs with version/width query params (CDN cruft)
    markdown = re.sub(r'https?://[^\s)]+\?v=\d+[^\s)]*', '', markdown)

    # Remove navigation links
    markdown = re.sub(r'\[Skip to .*?\]\(.*?\)', '', markdown)
    markdown = re.sub(r'\[Continue shopping\]\(.*?\)', '', markdown)

    # Remove cart UI text
    markdown = re.sub(r'Your cart is empty', '', markdown)
    markdown = re.sub(r'\d+Your cart is empty', '', markdown)

    # Remove standalone UI button text
    markdown = re.sub(r'\b(Close|Clear|ClearClose)\b', '', markdown)

    # Remove multiple consecutive newlines
    markdown = re.sub(r'\n{3,}', '\n\n', markdown)

    # Remove multiple consecutive spaces
    markdown = re.sub(r' {2,}', ' ', markdown)

    cleaned = markdown.strip()
    cleaned_length = len(cleaned)
    reduction = ((original_length - cleaned_length) / original_length * 100) if original_length > 0 else 0

    logger.debug(
        "Cleaned markdown",
        original_length=original_length,
        cleaned_length=cleaned_length,
        reduction_percent=f"{reduction:.1f}%"
    )

    return cleaned

class Scraper(Protocol):
    """An interface with scraping methods"""

    def scrape_and_search_site(self, query: str, limit: int = 5) -> FireResult:
        ...


class FirecrawlClient:
    """A concrete impl of a scraper class"""
    def __init__(self, api_key: str):
        logger.debug("Initialising Firecrawl Client...")
        self.client = Firecrawl(api_key=api_key)
        logger.info("Initialised Firecrawl Client Successful")

        self.firecrawl_prompt = "Extract the main Product Title and all core product details. Capture the full Description, current Price, and all selectable Variants (specifically Sizes, Colors, or Dimensions). Crucially, extract all text content hidden within collapsible UI elements, such as accordions, tabs, specifications lists, or 'read more' dropdowns. Ignore 'Related Products' or 'You May Also Like' sections."

    def scrape_and_search_site(self, query: str, limit: int = 5):
        """Some filtering x business logic in the concrete due to the size of response, structured response helps LLM as well"""
        logger.debug("Starting scraper", query=query, length_of_urls=limit)

        # this country code can change with an input param
        query_users_country = f"{query} :.au"

        if limit > 10:
            raise ValueError("Limit on pages cant be greater than 10 due to cost principle")

        excludeTag = [
            # Navigation & UI
            "header", "footer", "nav", "aside",
            ".skip-to-content", ".skip-link",
            ".cart", ".mini-cart", "#cart",
            ".search-bar", ".search-form",
            # Product variants/gallery (THE BIG ONE)
            ".product-gallery", ".product-thumbnails",
            ".variant-selector", ".color-swatches",
            ".size-selector", ".flavor-selector",
            ".product-images", ".image-gallery",
            # Reviews & Social
            ".reviews", "#reviews", ".customer-reviews",
            ".rating", ".star-rating",
            ".questions-and-answers", "#comments",
            ".related-products", ".upsell", ".recommendations",
            ".recently-viewed", ".you-may-like",
            ".newsletter", ".social-share", ".ads",
            # Navigation cruft
            ".breadcrumb", ".footer-links",
            ".pop-up", ".modal", ".overlay",
            # Common Shopify classes
            ".product-form__buttons",
            ".product-option",
        ]

        search = self.client.search(
            query = query_users_country,
            limit = limit,
            scrape_options = ScrapeOptions(
                only_main_content=True,
                formats=ScrapeFormats(
                    markdown=True,
                    remove_images=True, 
                ),
                exclude_tags=excludeTag,
                remove_base64_images=True,
                wait_for=0
            )
        )

        if not search:
            logger.info("No search results from scraper")
            raise FirecrawlError("No search returned")

        if not search.web:
            logger.info("successful search returned no url data")
            raise FirecrawlError("completed search returned no url data")

        if search.web:
            for result in search.web:
                if hasattr(result, 'markdown') and result.markdown:
                    result.markdown = clean_markdown(result.markdown)

        logger.info("Completed Scrape")
        return FireResult(
            data = search,
            query = query,
        )

    def get_urls_for_query(self, query: str, limit: int = 5):
        """A function to get urls from our scraper dependency"""
        logger.debug("Starting %s", inspect.stack()[0][3])
        query_with_location = f"{query} :.au"

        search_data = self.client.search(query=query_with_location, limit=limit,
            location="Sydney, Australia")
        return search_data

    def extract_from_url(self, url: str, prompt: str = None):
        """Extracting from Firecrawls smart extract"""
        return self.client.extract([url], prompt=self.firecrawl_prompt if prompt is None else prompt)

    def extract_from_urls(self, url_data: SearchData):
        """Extracting from Firecrawls smart extract"""
        urls = [url.url for url in url_data.web] if url_data.web else []
        logger.debug("Sending Urls For Scrape", urls=urls)

        return self.client.extract(
            urls=urls,
            prompt=self.firecrawl_prompt
        )

    #def gather_image()
