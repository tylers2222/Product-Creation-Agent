import inspect
import json
from typing import TypedDict, Dict
import structlog

from langgraph.graph import StateGraph, START, END
from langgraph.graph.state import Command

from product_agent.config.container import ServiceContainer
from product_agent.core.agent_configs.scraper import SCRAPER_AGENT_SYSTEM_PROMPT
from product_agent.models.llm_input import LLMInput
from product_agent.services.infrastructure.llm import llm_service
from product_agent.services.infrastructure.scraping import getting_urls_svc, batch_scraping_url_svc
from product_agent.services.orchestrators.content_extraction import analyse_markdowns_with_llm_svc



logger = structlog.getLogger(__name__)

class ScraperState(TypedDict):
    """State of scraper operations"""
    query:                      str
    limit:                      int
    urls:                       list
    current_index:              int = 0
    markdowns:                  list
    summaries:                  list[Dict]
    retry_count:                int = 0
    failed_urls:                list

class ScraperWorkflow:
    """
    A workflow definining an Ai based scraper

    Can add agents or LLMs to the workflow
    The steps are deterministic
    """
    def __init__(self, sc: ServiceContainer):
        self.workflow = StateGraph(ScraperState)
        self.workflow.add_node("get_urls", self.get_urls)
        self.workflow.add_node("get_markdowns", self.get_markdowns)
        self.workflow.add_node("analyse_markdowns", self.analyse_markdowns)
        self.workflow.add_node("needs_retry", self.needs_retry)
        self.workflow.add_node("log_run", self.log_run)

        self.workflow.add_edge(START, "get_urls")
        self.workflow.add_edge("get_urls", "get_markdowns")
        self.workflow.add_edge("get_markdowns", "analyse_markdowns")
        self.workflow.add_edge("analyse_markdowns", "needs_retry")
        self.workflow.add_edge("log_run", END)

        self.app = self.workflow.compile()

        self.service_container = sc

    async def get_urls(self, state: ScraperState):
        """
        Node that gets the urls for the search string
        """
        # Implement the get urls service
        logger.debug("Starting %s from langgraph node", inspect.stack()[0][3])

        urls = getting_urls_svc(
            query=state["query"],
            limit=state["limit"],
            url_provider=self.service_container.scraper
        )
        return {
            "urls": urls
        }
    async def get_markdowns(self, state: ScraperState):
        """Get the markdowns based on the urls"""
        logger.debug("Starting %s from langgraph node", inspect.stack()[0][3])
        
        ci = state["current_index"]
        len_summaries = len(state["summaries"])
        logger.debug("On the index %s", ci)

        results_left_to_get = 3 - len_summaries
        index_max = ci + results_left_to_get

        logger.debug("About to send requeset for index %s to %s", ci, index_max)
        urls_to_index = state["urls"][ci:index_max]
        logger.debug("Sending %s urls", len(urls_to_index), urls=urls_to_index)
        markdowns = batch_scraping_url_svc(urls=urls_to_index, scraper=self.service_container.scraper)
        return {
            "markdowns": markdowns,
            "current_index": index_max
        }

    async def analyse_markdowns(self, state: ScraperState):
        """Analyse the markdowns using an LLM"""
        node_key = "scraper_synthesis"
        logger.debug(
            "Starting %s from langgraph node", inspect.stack()[0][3],
            node_tag=node_key    
        )

        llm_config = self.service_container.llm_config(node_key)
        
        synthesis_results = await analyse_markdowns_with_llm_svc(
            state["markdowns"],
            llm=llm_config.client,
            model=llm_config.model
        )
        logger.debug(
            "Returned results from LLM",
            llm=llm_config.model,
            successful_count=len(synthesis_results.successful_scrapes)
        )

        return {
            "summaries": state["summaries"] + synthesis_results.successful_scrapes,
            "failed_urls": state["failed_urls"] + synthesis_results.failed_urls,
        }

    def needs_retry(self, state: ScraperState):
        """
        Check if we need to retry a scrape

        We add this node instead of handling all in a scraper and repeat monolith
        to preserve state in a better way
        """
        logger.debug("Starting %s from langgraph node", inspect.stack()[0][3])
        if len(state["summaries"]) >= 3:
            return Command(
                goto="summarise_workflow_run",
                update={"markdowns": []}
            )

        return Command(
            goto="get_markdowns",
            update={"retry_count": state.get("retry_count", 0) + 1}
        )

    def log_run(self, state: ScraperState):
        """Log the run"""
        # Workout a way to get the tenant id, request id in through ctx
        logger.info(
            "Completed ScraperWorkflow",
            query=state["query"],
            limit=state["limit"],
            total_urls=len(state["urls"]),
            successful_summaries=len(state["summaries"]),
            failed_urls=len(state["failed_urls"]),
            retry_count=state.get("retry_count", None)
        )
    
    # async def summarise_workflow_run(self, state: ScraperState):
    #     """
    #     Node that takes the run and gives you a summary
    #     of what happened
    #     """

    #     logger.debug("Starting %s from langgraph node", inspect.stack()[0][3])
    #     print("Type: ", type(state))
    #     print(json.dumps(state, indent=3, default=str))

    #     summary_result = await llm_service(
    #         LLMInput(   
    #             model=self.summary_model,
    #             # Need this to have a better system prompt
    #             user_query=f"{state}\n\n Give me a paragraph synopsis of what happened"
    #         ),
    #         llm=self.summary_llm
    #     )

    #     return {
    #         "summary_of_scrape": summary_result
    #     }

    async def start_run(self, query: str, limit: int = 10):
        """Start the graphs workflow"""
        return await self.app.ainvoke({
            "query": query,
            "limit": limit,
            "urls": [],
            "last_index": 0,
            "current_index": 0,
            "markdowns": [],
            "summaries": [],
            "retry_count": 0,
            "failed_urls": [],
        })