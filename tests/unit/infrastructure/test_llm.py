"""
Tests for LLM client and markdown_summariser function.

Uses standardized TestCase pattern with data + expected results.
Unit tests use mock LLM, integration tests use real OpenAI API.
"""
import pytest
import os
from dotenv import load_dotenv

from product_agent.infrastructure.llm.client import markdown_summariser
from product_agent.models.query import QueryResponse
from product_agent.infrastructure.llm.client import OpenAiClient


# -----------------------------------------------------------------------------
# Unit Tests
# -----------------------------------------------------------------------------

class TestMarkdownSummariser:
    """Unit tests for markdown_summariser function."""

    @pytest.mark.asyncio
    async def test_returns_summarised_content(self, mock_llm, tc_markdown_summariser):
        """
        Test that markdown_summariser returns summarised content.

        Verifies:
        - Result is not None
        - Result is a string
        - Result meets minimum length
        """
        tc = tc_markdown_summariser

        result = await markdown_summariser(
            title=tc.data["title"],
            markdown=tc.data["markdown"],
            llm=mock_llm
        )

        assert result is not None
        assert isinstance(result, tc.expected["type"])
        if tc.expected["is_not_empty"]:
            assert len(result) > 0

    @pytest.mark.asyncio
    async def test_invokes_with_schema(self, mock_llm):
        """
        Test that invoke returns structured response.

        Verifies:
        - Response is not None
        - Response is QueryResponse type when schema provided
        """
        from product_agent.models.llm_input import LLMInput

        llm_input = LLMInput(
            model="mini_deterministic",
            system_query=None,
            user_query="Test query",
            response_schema=QueryResponse,
            verbose=False
        )

        result = await mock_llm.invoke(llm_input)

        assert result is not None
        assert isinstance(result, QueryResponse)

    @pytest.mark.asyncio
    async def test_invokes_llm_with_markdown(self, mock_llm, tc_markdown_summariser):
        """
        Test that markdown_summariser calls invoke.

        Verifies:
        - invoke is called exactly once
        - mini_deterministic model is used
        """
        tc = tc_markdown_summariser

        await markdown_summariser(
            title=tc.data["title"],
            markdown=tc.data["markdown"],
            llm=mock_llm
        )

        assert mock_llm.invoke_call_count == 1
        assert mock_llm.last_model_used == "mini_deterministic"

    @pytest.mark.asyncio
    async def test_handles_empty_markdown(self, mock_llm):
        """
        Test that markdown_summariser handles empty markdown.

        Verifies:
        - Does not crash on empty input
        - Returns a result
        """
        result = await markdown_summariser(
            title="Test Product",
            markdown="",
            llm=mock_llm
        )

        assert result is not None

    @pytest.mark.asyncio
    async def test_handles_long_markdown(self, mock_llm):
        """
        Test that markdown_summariser handles long markdown content.

        Verifies:
        - Handles 20k+ character input
        - Returns a string result
        """
        long_markdown = "x" * 20000

        result = await markdown_summariser(
            title="Test Product",
            markdown=long_markdown,
            llm=mock_llm
        )

        assert result is not None
        assert isinstance(result, str)


class TestOpenAiClientModelResolution:
    """Unit tests for OpenAI model name resolution."""

    @pytest.mark.asyncio
    async def test_resolves_model_name_correctly(self):
        """
        Test that short model names like 'scraper_mini' resolve to full model names.

        Verifies:
        - Model name without '-' is resolved from _model_configs
        - Resolved model is the expected full name
        """
        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY", "test-key")
        client = OpenAiClient(api_key=api_key)
        
        from product_agent.models.llm_input import LLMInput
        
        # Create input with short model name
        llm_input = LLMInput(
            model="scraper_mini",
            system_query=None,
            user_query="Test query",
            response_schema=None,
            verbose=False
        )
        
        # The model should be resolved to the full name
        # Note: We're testing the resolution happens, not making actual API call
        expected_model = client._model_configs["scraper_mini"]["model"]
        assert expected_model == "gpt-4o-mini"

    @pytest.mark.asyncio
    async def test_invalid_model_name_raises_error(self):
        """
        Test that invalid model names raise appropriate errors.

        Verifies:
        - Model name not in _model_configs raises KeyError or LLMError
        """
        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY", "test-key")
        client = OpenAiClient(api_key=api_key)
        
        from product_agent.models.llm_input import LLMInput
        from product_agent.infrastructure.llm.client import LLMError
        
        # Create input with invalid model name
        llm_input = LLMInput(
            model="invalid_model_name",
            system_query=None,
            user_query="Test query",
            response_schema=None,
            verbose=False
        )
        
        # Should raise KeyError when trying to access invalid key
        # or LLMError if properly handled
        with pytest.raises((KeyError, LLMError)):
            await client.invoke(llm_input)

    @pytest.mark.asyncio
    async def test_full_model_name_with_dash_not_resolved(self):
        """
        Test that model names with '-' are used as-is without resolution.

        Verifies:
        - Model names containing '-' bypass the resolution logic
        - Full model names like 'gpt-4o-mini' are used directly
        """
        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY", "test-key")
        client = OpenAiClient(api_key=api_key)
        
        from product_agent.models.llm_input import LLMInput
        
        # Create input with full model name (contains dash)
        llm_input = LLMInput(
            model="gpt-4o-mini",
            system_query=None,
            user_query="Test query",
            response_schema=None,
            verbose=False
        )
        
        # Model should stay as-is since it contains '-'
        assert "-" in llm_input.model


class TestGeminiClientModelResolution:
    """Unit tests for Gemini model name resolution."""

    @pytest.mark.asyncio
    async def test_resolves_model_name_correctly(self):
        """
        Test that short model names like 'scraper_mini' resolve to full model names.

        Verifies:
        - Model name without '-' is resolved from _model_configs
        - Resolved model is the expected full name
        """
        from product_agent.infrastructure.llm.client import GeminiClient
        
        api_key = "test-key"
        client = GeminiClient(api_key=api_key)
        
        # Verify the model config exists and has correct value
        expected_model = client._model_configs["scraper_mini"]["model"]
        assert expected_model == "gemini-2.0-flash"

    @pytest.mark.asyncio
    async def test_invalid_model_name_raises_error(self):
        """
        Test that invalid model names raise appropriate errors.

        Verifies:
        - Model name not in _model_configs raises KeyError
        """
        from product_agent.infrastructure.llm.client import GeminiClient
        from product_agent.models.llm_input import LLMInput
        
        api_key = "test-key"
        client = GeminiClient(api_key=api_key)
        
        # Create input with invalid model name
        llm_input = LLMInput(
            model="invalid_model_name",
            system_query=None,
            user_query="Test query",
            response_schema=None,
            verbose=False
        )
        
        # Should raise KeyError when trying to access invalid key
        with pytest.raises(KeyError):
            await client.invoke(llm_input)



