import structlog

from agents.infrastructure.firecrawl_api.client import Scraper
from models.scraper_response import ScraperResponse, ProcessedResult
from agents.agent.llm import LLM, markdown_summariser

logger = structlog.getLogger(__name__)

def scrape_results_svc(search_str: str, scraper: Scraper, llm: LLM) -> ScraperResponse:
    logger.debug("Starting scrape_results_svc service", search_string_internet=search_str)

    fire_result = scraper.scrape_and_search_site(query=search_str)
    scrapes_list = fire_result.data.web
    logger.info(f"Found {len(scrapes_list)} urls in the {search_str} search")

    tokens = 0
    data_result = []
    failures: list[ProcessedResult] = []
    for idx, scrapes in enumerate(scrapes_list):
        if hasattr(scrapes, "markdown"):
            mrkdown = scrapes.markdown
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
        if len(mrkdown) > 15000:
            try:
                summarised_markdown = markdown_summariser(title=search_str, 
                    markdown=mrkdown, llm=llm)
                
                data_result.append(summarised_markdown)

            except AttributeError as a:
                # Can do something with this error in future
                raise AttributeError(a) from a

            except TypeError as t:
                # Can do something with this error in future
                raise TypeError(t) from t

            except Exception as e:
                logger.error(f"summarisation failed, adding full markdown", error=e)
                data_result.append(mrkdown)
                failures.append(ProcessedResult(index=idx, error=str(e)))
        else:
            data_result.append(mrkdown)
    
    logger.info("Completed scrape_results_svc")
    # token_estimate = tokens / 4
    return ScraperResponse(
        query = search_str,
        result = data_result,
        errors = failures if failures else None,
        all_failed = True if len(failures) == len(scrapes_list) else False,
        all_success = True if len(failures) == 0 else False
    )
    
