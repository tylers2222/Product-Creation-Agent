import structlog
import asyncio
from product_agent.infrastructure.image_scraper.client import ImageScraper
from product_agent.infrastructure.image_scraper.utils import get_bytes

logger = structlog.getLogger(__name__)

async def image_scraper_svc(
    image_scraper: ImageScraper,
    query: str,
    num_images: int = 5,
    headless: bool = True
) -> list[str]:
    """
    Scraping image links in the service layer

    Optimise the search the query using the formula
    product_query = f"{brand} {name} {variant} {size_ml} {size_oz}
    official product packaging front view"
    """

    if "official product packaging front view" not in query:
        query += " official product packaging front view"
        logger.debug("Adapted search query", adapted_search_query=query)

    return await image_scraper.get_google_images(
        query=query,
        num_images=num_images,
        headless=headless,
    )

async def image_to_bytes_svc(image_urls: list[str]):
    """Getting image base64 data in the service layer"""
    image_urls = [url for url in image_urls if url]
    coros = []
    for url in image_urls:
        if url == "":
            continue
        coros.append(get_bytes(image_url=url))

    coro_run =  await asyncio.gather(*coros, return_exceptions=True)

    result_dict = {}
    for idx, url in enumerate(image_urls):
        logger.debug("Results Type: %s", type(coro_run[idx]))
        if isinstance(coro_run[idx], Exception):
            logger.debug("Found product with exception", idx=idx, url=url)
            continue
        result_dict[url] = coro_run[idx]

    return result_dict