import inspect
import structlog
from typing import TypedDict, Dict

from langgraph.graph import StateGraph, START, END
from langgraph.graph.state import Command

from product_agent.services.infrastructure.scraping import getting_urls_svc, batch_scraping_url_svc
from product_agent.services.orchestrators.content_extraction import scrape_with_llm_svc

logger = structlog.getLogger(__name__)

class ScraperState(TypedDict):
    """State of scraper operations"""
    query:                      str
    limit:                      int
    urls:                       list
    current_index:              int
    markdowns:                  list
    summaries:                  list[Dict]
    retry_count:                int = 0
    failed_urls:                list
    summary_of_scrape:          str

class ScraperWorkflow:
    def __init__(self):
        self.workflow = StateGraph(ScraperState)
        self.workflow.add_node("get_urls", self.get_urls)
        self.workflow.add_node("get_markdowns", self.get_markdowns)
        self.workflow.add_node("analyse_markdowns", self.analyse_markdowns)
        self.workflow.add_node("needs_retry", self.needs_retry)
        self.workflow.add_node("summaise_scrape", self.summaise_scrape)

    async def get_urls(self, state: ScraperState):
        """
        Node that gets the urls for the search string
        """
        # Implement the get urls service
        logger.debug("Starting %s from langgraph node", inspect.stack()[0][3])

        urls = getting_urls_svc(query=state["query"], limit=state["limit"], url_provider=self.scraper)
        return {
            "urls": urls
        }
    async def get_markdowns(self, state: ScraperState):
        """Get the markdowns based on the urls"""
        logger.debug("Starting %s from langgraph node", inspect.stack()[0][3])
        # We are aiming for 3 results so get 3 results first
        markdowns = batch_scraping_url_svc(urls=state["urls"][:3], scraper=self.scraper)
        return {
            "markdowns": markdowns,
            "current_index": len(markdowns) - 1
        }

    async def analyse_markdowns(self, state: ScraperState):
        """Analyse the markdowns using an LLM"""
        

        return {
            "current_index": result.current_index,
            "summaries": result.summaries,
            "failed_urls": result.failed_urls
        }

    def needs_retry(self, state: ScraperState):
        """
        Check if we need to retry a scrape

        We add this node instead of handling all in a scraper and repeat monolith
        to preserve state in a better way
        """
        if len(state["summaries"]) > 2:
            return

        return Command(
            goto="analyse_markdowns",
            update={"retry_count": state.get("retry_count", 0) + 1}
        )

    def summaise_scrape(self, state: ScraperState):
        """
        Summarise the scrape into a summary by a fast LLM
        """

        return {
            "summary_of_scrape": result.summary_of_scrape
        }

    