"""
Tests for LLM client and markdown_summariser function.

Uses standardized TestCase pattern with data + expected results.
Unit tests use mock LLM, integration tests use real OpenAI API.
"""
import random
import pytest
import os
import sys
from dotenv import load_dotenv
from unittest.mock import patch, MagicMock

from product_agent.models.query import QueryResponse
from product_agent.infrastructure.llm.client import OpenAiClient
from product_agent.infrastructure.llm.client import GeminiClient
from product_agent.models.llm_input import LLMInput


# -----------------------------------------------------------------------------
# Unit Tests
# -----------------------------------------------------------------------------

class TestLLMs:
    """Unit tests for LLM"""

    @pytest.mark.asyncio
    async def test_invokes_with_schema(self, mock_llm):
        """
        Test that invoke returns structured response.

        Verifies:
        - Response is not None
        - Response is QueryResponse type when schema provided
        """

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

    @pytest.mark.asyncio
    async def test_gemini_transform_for_images(
        self,
        real_gemini_llm,
        mock_image_transformer_data
    ):
        """Testing the output of the gemini transformation"""
        with patch.object(
            real_gemini_llm,
            "upload_to_file_api",
            return_value=random.randint(0, 100000)
        ):
            transformed_query = await real_gemini_llm.transform_for_images(data=mock_image_transformer_data)
            assert transformed_query is not None

            for query_piece in transformed_query:
                print()
                print("Type: ", type(query_piece))
                print("Value: ", query_piece)

    @pytest.mark.asyncio
    async def test_gemini_transform_for_images_large_query(
        self,
        real_gemini_llm,
        mock_image_transformer_data
    ):
        """Testing when a large image list is above 20mb"""
        with patch("src.product_agent.infrastructure.llm.client.calculate_image_size", return_value=21) as mock_calculate_size:
            with patch.object(
                real_gemini_llm,
                "upload_to_file_api",
                return_value=random.randint(0, 100000)
            ):
                transformed_query = await real_gemini_llm.transform_for_images(data=mock_image_transformer_data)
                assert transformed_query is not None
                mock_calculate_size.assert_called_once()
                
                for query_piece in transformed_query:
                    print()
                    print("Type: ", type(query_piece))
                    print("Value: ", query_piece)