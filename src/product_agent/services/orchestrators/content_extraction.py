"""Content extraction orchestrator that coordinates web scraping with LLM-based information extraction."""

import asyncio
import inspect
import logging

from product_agent.core.agent_configs.scraper import SCRAPER_AGENT_SYSTEM_PROMPT
from product_agent.models.llm_input import LLMInput
from product_agent.infrastructure.firecrawl.client import Scraper
from product_agent.infrastructure.llm.client import LLM
from product_agent.core.exceptions import NoScraperResult

from ..infrastructure.scraping import scrape_results_svc

logger = logging.getLogger(__name__)

async def analyse_markdowns_with_llm_svc(markdowns: list[str], llm: LLM, model: str):
    """Analysing markdown with LLMs in the service layer"""
    logger.debug("Starting %s", inspect.stack()[0][3], len_urls=len(markdowns))
    coros = []
    for markdown in markdowns:
        llm_config = LLMInput(
            model=model,
            system_query=SCRAPER_AGENT_SYSTEM_PROMPT,
            user_query=f"Analyse this markdown for product details and return json\n\n{markdown}"
        )
        coros.append(llm.invoke(llm_input=llm_config))

    scrapes = asyncio.gather(coros)
    logger.debug("Completed scrape in %s", inspect.stack()[0][3], len_scrapes=len(scrapes))
    return scrapes
Integration and unit test this service to see how it goes with system caching

async def scrape_with_llm_svc(search_str: str,
    scraper: Scraper,
    llm: LLM,
    model: str,
    limit_results=5) -> list:
    """
    Orchestrates web scraping followed by LLM-based product information extraction.

    This orchestrator coordinates two services: first scraping markdown content from web searches,
    then using an LLM to extract structured product information from each scraped page in parallel.

    Args:
        search_str: The string to put into google search
        scraper: Scraper dependency for web scraping
        llm: LLM dependency for information extraction

    Returns:
        List of LLM responses containing extracted product information from each scraped page

    Raises:
        NoScraperResult: When all scraping attempts fail
    """
    logger.debug("Starting %s", inspect.stack()[0][3],
        search_str=search_str, limit_results=limit_results)

    scrape_result = scrape_results_svc(search_str=search_str, scraper=scraper,
        limit_results=limit_results)
    if scrape_result.all_failed:
        raise NoScraperResult(search_query=search_str)

    coros = []
    for sites in scrape_result.result:
        user_query = f"{sites}\n\nReturn the product information from this markdown"
        coros.append(llm.invoke(LLMInput(
            model=model,
            system_query=SCRAPER_AGENT_SYSTEM_PROMPT,
            user_query=user_query
        )))
    
    logger.debug("About to start parralel synthesis", length=len(coros))

    results = await asyncio.gather(*coros)
    logger.info("Returned results from the LLM", length=len(results))
    return results
