import pytest

from product_agent.services.workflows.scraper import ScraperWorkflow

@pytest.mark.integration
class TestScraperWorkflow:
    @pytest.mark.asyncio
    async def test_full_workflow(self, real_service_container):
        """
        Test the full workflow in the integration layer
        """
        query = "Optimum Nutrition Gold Standard 100% Whey"

        workflow_result = await ScraperWorkflow(
            sc=real_service_container,
            scraper_llm="gemini",
            scraper_model="gemini-2.5-flash",
            summary_llm="gemini",
            summary_model="gemini-2.5-flash",
        ).start_run(query)

        assert workflow_result is not None

        print(workflow_result)