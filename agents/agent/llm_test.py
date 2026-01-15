"""
Tests for LLM client and markdown_summariser function.

Uses standardized TestCase pattern with data + expected results.
Unit tests use mock LLM, integration tests use real OpenAI API.
"""
import pytest

from agents.agent.llm import markdown_summariser
from models.product_generation import QueryResponse


# -----------------------------------------------------------------------------
# Unit Tests
# -----------------------------------------------------------------------------

class TestMarkdownSummariser:
    """Unit tests for markdown_summariser function."""

    def test_returns_summarised_content(self, mock_llm, tc_markdown_summariser):
        """
        Test that markdown_summariser returns summarised content.

        Verifies:
        - Result is not None
        - Result is a string
        - Result meets minimum length
        """
        tc = tc_markdown_summariser

        result = markdown_summariser(
            title=tc.data["title"],
            markdown=tc.data["markdown"],
            llm=mock_llm
        )

        assert result is not None
        assert isinstance(result, tc.expected["type"])
        if tc.expected["is_not_empty"]:
            assert len(result) > 0

    def test_invokes_mini(self, mock_llm):
        """
        Test that invoke_mini returns structured response.

        Verifies:
        - Response is not None
        - Response is QueryResponse type when schema provided
        """
        user_query = "Test query"

        result = mock_llm.invoke_mini(
            system_query=None,
            user_query=user_query,
            response_schema=QueryResponse
        )

        assert result is not None
        assert isinstance(result, QueryResponse)

    def test_invokes_llm_mini_with_markdown(self, mock_llm, tc_markdown_summariser):
        """
        Test that markdown_summariser calls invoke_mini.

        Verifies:
        - invoke_mini is called exactly once
        """
        tc = tc_markdown_summariser

        markdown_summariser(
            title=tc.data["title"],
            markdown=tc.data["markdown"],
            llm=mock_llm
        )

        assert mock_llm.invoke_mini_call_count == 1

    def test_handles_empty_markdown(self, mock_llm):
        """
        Test that markdown_summariser handles empty markdown.

        Verifies:
        - Does not crash on empty input
        - Returns a result
        """
        result = markdown_summariser(
            title="Test Product",
            markdown="",
            llm=mock_llm
        )

        assert result is not None

    def test_handles_long_markdown(self, mock_llm):
        """
        Test that markdown_summariser handles long markdown content.

        Verifies:
        - Handles 20k+ character input
        - Returns a string result
        """
        long_markdown = "x" * 20000

        result = markdown_summariser(
            title="Test Product",
            markdown=long_markdown,
            llm=mock_llm
        )

        assert result is not None
        assert isinstance(result, str)


# -----------------------------------------------------------------------------
# Integration Tests
# -----------------------------------------------------------------------------

@pytest.mark.integration
class TestMarkdownSummariserIntegration:
    """
    Integration tests using real OpenAI API.

    These tests require OPENAI_API_KEY to be set.
    Run with: pytest -m integration
    """

    @pytest.fixture
    def real_llm(self):
        """Create a real LLM client."""
        from agents.agent.llm import llm_client
        return llm_client()

    def test_summarises_product_markdown(self, real_llm, tc_markdown_summariser):
        """
        Test summarising actual product markdown content.

        Verifies:
        - Real LLM returns summarised content
        - Result is a non-empty string
        """
        tc = tc_markdown_summariser

        result = markdown_summariser(
            title=tc.data["title"],
            markdown=tc.data["markdown"],
            llm=real_llm
        )

        assert result is not None
        assert isinstance(result, tc.expected["type"])
        assert len(result) >= tc.expected["min_length"]
