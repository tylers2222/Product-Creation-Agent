"""
Content extraction orchestrator that coordinates 
web scraping with LLM-based information extraction.
"""

import asyncio
import inspect
import logging
from product_agent.services.infrastructure.llm import llm_service
from pydantic import BaseModel

from product_agent.core.agent_configs.scraper import SCRAPER_AGENT_SYSTEM_PROMPT
from product_agent.models.llm_input import LLMInput
from product_agent.infrastructure.firecrawl.client import Scraper
from product_agent.infrastructure.llm.client import LLM
from product_agent.core.exceptions import NoScraperResult
from product_agent.models.scraper import ScraperResponse, ScraperSynthesisResponse

from ..infrastructure.scraping import scrape_results_svc

logger = logging.getLogger(__name__)

class ScrapedResults(BaseModel):
    successful_scrapes:     list
    failed_urls:            list

async def analyse_markdowns_with_llm_svc(markdowns: list[str], llm: LLM, model: str) -> ScrapedResults:
    """Analysing markdown with LLMs in the service layer"""
    logger.debug("Starting %s", inspect.stack()[0][3], len_urls=len(markdowns))
    coros = []
    for markdown in markdowns:
        llm_config = LLMInput(
            model=model,
            system_query=SCRAPER_AGENT_SYSTEM_PROMPT,
            user_query=f"Analyse this markdown for product details and return json\n\n{markdown}",
            response_schema=ScraperSynthesisResponse
        )
        coros.append(llm_service(llm_config, llm))

    scrapes =  await asyncio.gather(*coros)

    success_scrapes = []
    failed_scrapes = []
    for scrape in scrapes:
        if scrape.description is None:
            failed_scrapes.append(scrape.url)
            continue
        
        success_scrapes.append(scrape)

    logger.debug("Completed scrape in %s", inspect.stack()[0][3], len_scrapes=len(success_scrapes), len_failed=len(failed_scrapes))
    return ScrapedResults(
        successful_scrapes=success_scrapes,
        failed_urls=failed_scrapes
    )

async def scrape_with_llm_svc(search_str: str,
    scraper: Scraper,
    llm: LLM,
    model: str,
    limit_results=5) -> ScrapedResults:
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
        coros.append(llm_service(
            LLMInput(
                model=model,
                system_query=SCRAPER_AGENT_SYSTEM_PROMPT,
                user_query=user_query,
                response_schema=ScraperSynthesisResponse
            ),
            llm=llm
        ))
    
    logger.debug("About to start parralel synthesis", length=len(coros))

    results = await asyncio.gather(*coros)
    logger.info("Returned results from the LLM", length=len(results))
    return results
