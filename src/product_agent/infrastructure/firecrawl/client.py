import inspect
import json
import requests
from firecrawl import Firecrawl
from firecrawl.types import ScrapeOptions, ScrapeFormats, SearchData
from typing import List, Protocol
import structlog
from kadoa_sdk import KadoaClient, KadoaSdkConfig, ExtractionOptions
from .exceptions import FirecrawlError
from .schemas import FireResult
from .utils import clean_markdown

logger = structlog.get_logger(__name__)


class Scraper(Protocol):
    """An interface with scraping methods"""
    def scrape_and_search_site(self, query: str, limit: int = 5) -> FireResult:
        ...
    def scraper_url_to_markdown(self, url: str) -> str:
        ...
    def batch_scraper_url_to_markdown(self, urls: List[str]) -> list[str]:
        ...

class UrlProvider(Protocol):
    """An interface with url getting methods"""
    def get_urls_for_query(self, query: str, limit: int = 5) -> list:
        ...

excludeTag = [
    # Navigation & UI
    "header", "footer", "nav", "aside",
    ".skip-to-content", ".skip-link",
    ".cart", ".mini-cart", "#cart",
    ".search-bar", ".search-form",
    # Product variants/gallery (THE BIG ONE)
    ".variant-selector", ".color-swatches",
    ".size-selector", ".flavor-selector",
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

class FirecrawlClient:
    """A concrete impl of a scraper class"""
    def __init__(self, api_key: str):
        logger.debug("Initialising Firecrawl Client...")
        self.client = Firecrawl(api_key=api_key)
        logger.info("Initialised Firecrawl Client Successful")

        self.firecrawl_prompt = "Extract the main Product Title and all core product details. Capture the full Description, current Price, and all selectable Variants (specifically Sizes, Colors, or Dimensions). Crucially, extract all text content hidden within collapsible UI elements, such as accordions, tabs, specifications lists, or 'read more' dropdowns. Ignore 'Related Products' or 'You May Also Like' sections."

    def scraper_url_to_markdown(self, url: str) -> str:
        """Scrape a single urls markdown"""
        logger.debug("Starting %s", inspect.stack()[0][3], url=url)
        markdown = self.client.scrape(url=url, 
            formats=["markdown"],
            only_main_content=True,
            exclude_tags=excludeTag,
            remove_base64_images=True
        )
        return markdown.markdown.replace("\n", "")

    def batch_scraper_url_to_markdown(self, urls: List[str]) -> list[str]:
        """Batch scraping urls"""
        logger.debug("Starting %s", inspect.stack()[0][3], urls=urls)
        markdowns = self.client.batch_scrape(urls, 
            formats=["markdown"], wait_timeout=120,
            only_main_content=True,
            exclude_tags=excludeTag,
            remove_base64_images=True
        )
        return [item.markdown.replace("\n", "") for item in markdowns.data]

    def scrape_and_search_site(self, query: str, limit: int = 5):
        """Some filtering x business logic in the concrete due to the size of response, structured response helps LLM as well"""
        logger.debug("Starting scraper", query=query, length_of_urls=limit)

        if limit > 10:
            raise ValueError("Limit on pages cant be greater than 10 due to cost principle")

        search = self.client.search(
            query = query,
            limit = limit,
            scrape_options = ScrapeOptions(
                only_main_content=True,
                formats=ScrapeFormats(
                    markdown=True,
                    remove_images=True, 
                ),
                exclude_tags=excludeTag,
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

    def get_urls_for_query(self, query: str, limit: int = 5) -> list:
        """A function to get urls from our scraper dependency"""
        logger.debug("Starting %s", inspect.stack()[0][3])
        query_with_location = f"{query} buy online:.au"

        search_data = self.client.search(query=query_with_location, limit=limit,
            location="Sydney, Australia")
        return search_data.web

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

# ------------------------------------------------------------------------
# NOT USING
# ------------------------------------------------------------------------
class KadoaScraper:
    """Ai scraper made by Kadoa for easier extraction"""
    def __init__(self, api_key):
        self.api_key = api_key
        self.client = KadoaClient(KadoaSdkConfig(api_key=api_key))
        self.product_prompt = "Extract the main Product Title and all core product details. Capture the full Description, current Price, and all selectable Variants (specifically Sizes, Colors, or Dimensions). Crucially, extract all text content hidden within collapsible UI elements, such as accordions, tabs, specifications lists, or 'read more' dropdowns. Ignore 'Related Products' or 'You May Also Like' sections."
        logger.debug("Initialised Kadoa Client")

    def scrape_url_http(self, url):
        """At the time of this comment SDK is bugged, using HTTP"""
        logger.debug("Staring %s", inspect.stack()[0][3])
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        
        fields = [
            {"name": "title", "dataType": "STRING", "description": "Product title", "example": "Gold Standard 100% Whey Protein Powder"},
            {"name": "description", "dataType": "STRING", "description": "Full product description including features, benefits, ingredients, and any collapsible content", "example": "Optimum Nutrition Gold Standard 100% Whey is the world's best-selling whey protein powder... Includes detailed ingredients list, nutritional information, and benefits."},
            {"name": "price", "dataType": "MONEY", "description": "Current product price"},
            {"name": "variants", "dataType": "ARRAY", "description": "All product variants from dropdowns/selectors including sizes (e.g., 1lb, 2lb, 5lb), flavors (e.g., Chocolate, Vanilla, Strawberry), colors, or any other selectable options with their associated prices and SKUs", "example": "[{\"size\": \"2lb\", \"flavor\": \"Extreme Milk Chocolate\", \"price\": \"$59.99\", \"sku\": \"ON-GS-2LB-EMC\"}, {\"size\": \"5lb\", \"flavor\": \"Vanilla Ice Cream\", \"price\": \"$119.99\", \"sku\": \"ON-GS-5LB-VIC\"}]"},
            {"name": "ingredients", "dataType": "STRING", "description": "Product ingredients list from any dropdown or expandable section", "example": "Whey Protein Isolate, Cocoa (Processed with Alkali), Natural and Artificial Flavors, Lecithin, Salt, Acesulfame Potassium, Sucralose"},
            {"name": "nutritionalInfo", "dataType": "STRING", "description": "Nutritional information including calories, protein, carbs, fats from any expandable sections", "example": "Per serving: 120 calories, 24g protein, 3g carbs, 1g fat"},
            {"name": "benefits", "dataType": "STRING", "description": "Product benefits and features from any collapsible sections or tabs", "example": "24g of protein per serving, supports muscle recovery, ideal post-workout nutrition"},
            {"name": "specifications", "dataType": "STRING", "description": "Product specifications including dimensions, weight, serving size from any dropdown or expandable sections", "example": "Serving size: 1 scoop (31g), Servings per container: 32, Dimensions: 10.5 x 6.5 x 6.5 inches"}
        ]
        
        data = {
            "urls": [url],
            "name": "Extraction",
            "entity": "Product",
            "fields": fields,
            "userPrompt": self.product_prompt
        }

        response = requests.post(url="https://api.kadoa.com/v4/workflows",
            headers=headers, json=data, timeout=300)
        if response.status_code > 299:
    
            try:
                response_body = response.json()
            except (ValueError, json.JSONDecodeError):
                response_body = response.text
            
            logger.error("Failed to request url",
                        url=url,
                        status_code=response.status_code,
                        response_body=response_body,
                        headers=response.headers)
            raise ValueError(f"Bad Response Code {response.status_code}: {response_body}")

        logger.info("Completed %s", inspect.stack()[0][3])
        return response.json()

    def scrape_url(self, url: str):
        """Scrape a single url with sdk"""
        result = self.client.extraction.run(
            ExtractionOptions(
                urls=[url],
                name="Extraction",
                user_prompt=self.product_prompt,
                limit=10,
            )
        )

        return result

    def scrape_urls(self, urls: list[str]):
        """Scrape multiple urls"""
        result = self.client.extraction.run(
            ExtractionOptions(
                urls=[urls],
                name="Extraction",
                user_prompt=self.product_prompt,
                limit=10,
            )
        )

        return result
