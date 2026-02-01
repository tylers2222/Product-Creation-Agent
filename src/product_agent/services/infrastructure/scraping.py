import structlog

from product_agent.infrastructure.firecrawl.client import Scraper, UrlProvider
from product_agent.models.scraper import ScraperResponse, ProcessedResult

logger = structlog.getLogger(__name__)

def getting_urls_svc(query: str, limit: int, url_provider: UrlProvider):
    """Url getting in the service layer"""
    if query == "":
        raise ValueError("Query was empty")

    urls = url_provider.get_urls_for_query(query=query, limit=limit)
    logger.debug("Completed url scrape", urls=urls)
    return urls

def scraping_url_svc(url: str, scraper: Scraper):
    """Scraping a single url in the service layer"""
    if url == "":
        raise ValueError("Url was empty")

    markdown = scraper.scraper_url_to_markdown(url=url)
    logger.debug("Markdown recieved", len_markdown=len(markdown))
    return markdown

def batch_scraping_url_svc(urls: list[str], scraper: Scraper):
    """Batch scraping urls in the service layer"""
    if len(urls) == 0:
        raise ValueError("No Urls recieved")

    markdowns = scraper.batch_scraper_url_to_markdown(urls=urls)
    logger.debug("Recived markdowns", len_markdowns=len(markdowns))
    return markdowns

def scrape_results_svc(search_str: str,
        scraper: Scraper, limit_results: int = 5) -> ScraperResponse:
    """
    Markdown scraper in the service layer

    args:
        search_str: The string that will serve as the google search
        scraper: Scraper Dependency
        limit_results: How many urls to scrape
    """
    logger.debug("Starting scrape_results_svc service", search_string_internet=search_str)

    query_users_country = f"{search_str} :.au"

    fire_result = scraper.scrape_and_search_site(query=query_users_country, limit=limit_results)
    scrapes_list = fire_result.data.web
    logger.info(f"Found {len(scrapes_list)} urls in the {query_users_country} search")

    tokens = 0
    data_result = []
    failures: list[ProcessedResult] = []
    for idx, scrapes in enumerate(scrapes_list):
        if hasattr(scrapes, "markdown"):
            mrkdown = scrapes.markdown
            data_result.append(mrkdown)
        else:
            logger.info("%s in the scrape loop didnt have a markdown", idx)
            continue

        if not mrkdown:
            metadata = scrapes.metadata
            url = getattr(metadata, 'url', 'unknown') if metadata else 'unknown'
            logger.warn("URL didnt have markdown...", url=url)
            failures.append(ProcessedResult(index=idx, error="No markdown content"))
            continue

        tokens += len(mrkdown)
    
    logger.info("Completed scrape_results_svc")
    # token_estimate = tokens / 4
    return ScraperResponse(
        query = query_users_country,
        result = data_result,
        errors = failures if failures else None,
        all_failed = True if len(failures) == len(scrapes_list) else False,
        all_success = True if len(failures) == 0 else False
    )
