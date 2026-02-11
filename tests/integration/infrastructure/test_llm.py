import asyncio
import io
import json
from product_agent.core.agent_configs.scraper import SCRAPER_AGENT_SYSTEM_PROMPT
from product_agent.models.scraper import ScraperResponse
from pydantic import BaseModel, Field
import pytest

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
        with open("tests/data/test_markdowns.json", encoding="utf-8") as data:
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

    @pytest.mark.asyncio
    async def test_gemini_with_pydantic(self, real_gemini_llm):
        """
        Test invoking gemini with pydantic response
        """
        with open("tests/data/test_markdowns.json", encoding="utf-8") as data:
            markdown = json.load(data)
            markdown_data = markdown["markdown"]

        llm_input = LLMInput(
            model="gemini-2.5-flash",
            system_query=SCRAPER_AGENT_SYSTEM_PROMPT,
            user_query=markdown_data + "\n\nScrape this page",
            response_schema=ScraperResponse
        )
        gemini_response = await real_gemini_llm.invoke(llm_input)
        assert gemini_response is not None
        assert isinstance(gemini_response, ScraperResponse)

        print(gemini_response.model_dump_json(indent=3))

    @pytest.mark.asyncio
    async def test_upload_file_to_api(
        self,
        real_gemini_llm
    ):
        """Test pushing an image to the file api"""
        with open("tests/integration/infrastructure/images/image_1.jpg", "rb") as image_bytes:
            image_bytes = image_bytes.read()

        url = "evelynfaye.com"
        file_result = await real_gemini_llm.upload_to_file_api(
            url=url,
            image_file=io.BytesIO(image_bytes)
        )

        assert file_result is not None
        print("Type: ", type(file_result))
        print()
        print("Dir: ", [method for method in dir(file_result) if not method.startswith("_")])
        print()
        print(file_result)

    @pytest.mark.asyncio
    async def test_transform_for_images_gemini(
        self,
        real_gemini_llm,
        real_image_transformer_data
    ):
        """Test the client specific transform for its image data"""
        gemini_specific_query = await real_gemini_llm.transform_for_images(
            data=real_image_transformer_data
        )

        assert gemini_specific_query is not None
        assert isinstance(gemini_specific_query, list)

        for query_part in gemini_specific_query:
            print()
            print(query_part)

    @pytest.mark.asyncio
    async def test_transform_for_images_open_ai(
        self,
        real_openai_llm,
        mock_image_transformer_data
    ):
        """Test the client specific transform for its image data"""
        open_ai_specific_query = await real_openai_llm.transform_for_images(
            data=mock_image_transformer_data
        )

        assert open_ai_specific_query is not None
        assert isinstance(open_ai_specific_query, list)

        for query_part in open_ai_specific_query:
            print()
            print(query_part)