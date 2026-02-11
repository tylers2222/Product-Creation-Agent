from product_agent.infrastructure.firecrawl.client import Scraper
from product_agent.services.orchestrators.content_extraction import ScrapedResults
import pytest
from unittest.mock import patch

from product_agent.services.workflows.scraper import ScraperWorkflow

class TestScraperWorkflow:
    @pytest.mark.asyncio
    @patch("product_agent.services.workflows.scraper.analyse_markdowns_with_llm_svc")
    async def test_full_workflow(self,
        mock_analyse_svc,
        mock_service_container,
        sample_markdowns,
        sample_urls
    ):
        """Testing the scraper workflow start to finish"""
        # Configure mock scraper to return test data
        mock_service_container.scraper.get_urls_for_query.return_value = sample_urls
        mock_service_container.scraper.batch_scraper_url_to_markdown.side_effect = [
            # Return 3 markdowns in the first run
            sample_markdowns,
            # Return 1 in the second run assuming 2 succeed in analysis step
            sample_markdowns[2]
        ]

        # Configure mock LLM to return test data
        mock_service_container.llm["gemini"].return_value = {
            "content": "Summary of scraped content"
        }

        mock_analyse_svc.side_effect = [
            # Run 1
            ScrapedResults(
                successful_scrapes = ["Summary 1", "Sumamary 2"],
                failed_urls=["Failed 1"]
            ),
            # Run 2
            ScrapedResults(
                successful_scrapes = ["Summary 3"],
                failed_urls= []
            )
        ]

        workflow_result = await ScraperWorkflow(
            sc=mock_service_container,
            scraper_llm="gemini",
            scraper_model="gemini-2.5-flash",
            summary_llm="gemini",
            summary_model="gemini-2.5-flash"
        ).start_run(query="Optimum Nutrition 2.5k Whey")

        assert workflow_result is not None
        print("Type: ", type(workflow_result))
        print("Result: ", workflow_result)

        assert workflow_result["current_index"] > 0
        assert workflow_result["last_index"] > 0

        assert len(workflow_result["failed_urls"]) > 0

        assert mock_analyse_svc.call_count == 2

    @pytest.mark.asyncio
    @patch("product_agent.services.workflows.scraper.getting_urls_svc")
    @patch("product_agent.services.workflows.scraper.batch_scraping_url_svc")
    @patch("product_agent.services.workflows.scraper.analyse_markdowns_with_llm_svc")
    async def test_two_retries(
        self,
        mock_analyse_svc,
        mock_markdown_svc,
        mock_urls_svc,
        mock_service_container,
        sample_urls
    ):
        """
        Test multi retry scraper
        
        Hit the retry node twice
        """

        # This only gets called once
        mock_urls_svc.return_value = sample_urls

        mock_analyse_svc.side_effect = [
            ScrapedResults(
                successful_scrapes=["Summary 1"],
                failed_urls=["url 1", "url 2"]
            ),
            ScrapedResults(
                successful_scrapes=["Summary 2"],
                failed_urls=[]
            ),
            ScrapedResults(
                successful_scrapes=["Summary 3"],
                failed_urls=[]
            ),
        ]

        mock_markdown_svc.side_effect = [
            ["fasfadsfas", "asfasfvaewrf", "awef"],
            ["asvewafewrw"],
            ["hiuerhngunvb"]
        ]

        scraper_result = await ScraperWorkflow(
            sc=mock_service_container,
            scraper_llm="gemini",
            scraper_model="gemini-2.5-flash",
            summary_llm="gemini",
            summary_model="gemini-2.5-flash"
        ).start_run("This is a placeholder query")

        assert scraper_result is not None
        assert scraper_result["retry_count"] > 1

        assert mock_analyse_svc.call_count > 1

        print(scraper_result)