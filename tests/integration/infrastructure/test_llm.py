import asyncio
import json
from product_agent.core.agent_configs.scraper import SCRAPER_AGENT_SYSTEM_PROMPT
from pydantic import BaseModel, Field
import pytest
import os
from dotenv import load_dotenv

from product_agent.models.llm_input import LLMInput
from product_agent.infrastructure.llm.client import OpenAiClient
from product_agent.infrastructure.llm.client import GeminiClient

# -----------------------------------------------------------------------------
# Integration Tests
# -----------------------------------------------------------------------------

@pytest.mark.integration
class TestLLMs:
    """
    Integration tests using real OpenAI API.

    These tests require OPENAI_API_KEY to be set.
    Run with: pytest -m integration
    """

    @pytest.mark.asyncio
    async def test_openai_ping(self, real_openai_llm):
        """Ping Open Ai to test for basic connection"""
        llm_input = LLMInput(
            model="max_deterministic",
            user_query="Ping",
            verbose=True
        )
        response = await real_openai_llm.invoke(llm_input=llm_input)
        assert response is not None
        print("Response Type: ", type(response))
        print(response)

    @pytest.mark.asyncio
    async def test_openai_to_struct(self, real_openai_llm):
        """Test that the llm returns a pydantic model"""
        class Structure(BaseModel):
            """Model wanted"""
            response: str = Field(description="Response to the question")
            chars: int = Field(description="How many characters the response had")

        llm_input = LLMInput(
            model="max_deterministic",
            user_query="Ping",
            response_schema=Structure,
            verbose=True
        )
        response = await real_openai_llm.invoke(llm_input=llm_input)
        assert response is not None
        assert isinstance(response, Structure)
        print(response)

    @pytest.mark.asyncio
    async def test_gemini_ping(self, real_gemini_llm):
        """Testing sending ping to gemini LLM"""
        model = "gemini-2.0-flash"
        result = await real_gemini_llm.invoke(llm_input=LLMInput(
            model=model,
            user_query="Ping"
        ))

        assert result is not None
        print("Result Type: ", type(result))
        print()
        print("Dir: ", dir(result))
        print()
        print("Result: ", result)
        print()
        print("Result.text: ", result.text)

    @pytest.mark.asyncio
    async def test_all_gemini_models_with_markdown(self,
        real_gemini_llm,
        gemini_models):
        """
        Test that loads in a markdown and LLM synthesises
        Came about because early gemini models sucked at
        being a scraper

        Run this test with bash output to a file
        Big return
        """
        print("Length Of Gemini Models", len(gemini_models))
        with open("tests/integration/infrastructure/test_markdowns.json", encoding="utf-8") as data:
            markdown = json.load(data)
            print("Data Loaded: ", type(markdown))
            markdown_data = markdown["markdown"]
            print("Markdown Data Loaded: ", type(markdown_data))

        coros = []
        for model in gemini_models:
            print()
            print("Starting With Model: ", model)

            llm_input = LLMInput(
                model=model,
                system_query=SCRAPER_AGENT_SYSTEM_PROMPT,
                user_query=f"Here's a markdown \n\n{markdown_data}\n\nReturn a product data scrape in json format",
            )
            response_coro = real_gemini_llm.invoke(llm_input)
            coros.append(response_coro)

        results = await asyncio.gather(*coros)
        print("Length Of Results Returned: ", len(results))

        for idx, result in enumerate(results):
            print()
            print()
            print("-"*60)
            print("Model: ", gemini_models[idx])
            print("Type: ", type(result))
            print("Result: ", result)


@pytest.mark.integration
class TestLLMClientResolution:
    def test_client_resolution_all(self, real_openai_llm, real_gemini_llm):
        """Test all the LLM clients getting a model"""
        
