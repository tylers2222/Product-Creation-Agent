"""
Tests for vector database service layer functions.

Uses standardized TestCase pattern with data + expected results.
"""
import pytest

from services.internal.vector_db import similarity_search_svc, product_similarity_threshold_svc


# -----------------------------------------------------------------------------
# Unit Tests
# -----------------------------------------------------------------------------

class TestSimilaritySearchService:
    """Tests for similarity_search_svc function."""

    def test_returns_documents(self, mock_vector_db, tc_similarity_search):
        """
        Test that similarity_search_svc returns documents.

        Verifies:
        - Results are not None
        - At least minimum results returned
        """
        tc = tc_similarity_search

        results = similarity_search_svc(
            vector_query=tc.data["vector_query"],
            results_wanted=tc.data["results_wanted"],
            vector_db=mock_vector_db
        )

        assert results is not None
        assert len(results) >= tc.expected["min_results"]

    def test_returns_within_limit(self, mock_vector_db, tc_similarity_search):
        """
        Test that the service respects the results limit.

        Verifies:
        - Results don't exceed requested count
        """
        tc = tc_similarity_search

        results = similarity_search_svc(
            vector_query=tc.data["vector_query"],
            results_wanted=tc.data["results_wanted"],
            vector_db=mock_vector_db
        )

        assert len(results) <= tc.expected["max_results"]

    def test_results_have_payload(self, mock_vector_db, tc_similarity_search):
        """
        Test that results include payload data.

        Verifies:
        - Each result has a payload attribute
        """
        tc = tc_similarity_search

        results = similarity_search_svc(
            vector_query=tc.data["vector_query"],
            results_wanted=tc.data["results_wanted"],
            vector_db=mock_vector_db
        )

        if tc.expected["has_payload"]:
            for result in results:
                assert hasattr(result, 'payload')
                assert result.payload is not None


class TestProductSimilarityThreshold:
    """Tests for product_similarity_threshold_svc function."""

    def test_returns_result_above_threshold(self, mock_vector_db, sample_embedding):
        """
        Test that product_similarity_threshold_svc returns result when above threshold.

        Verifies:
        - Result is not None when similarity exceeds 0.92
        - Result has score attribute
        - Result has product_name attribute
        """
        result = product_similarity_threshold_svc(
            vector_query=sample_embedding,
            vector_db=mock_vector_db
        )

        assert result is not None
        assert hasattr(result, 'score')
        assert hasattr(result, 'product_name')
        assert result.score > 0.92

    def test_result_score_value(self, mock_vector_db, sample_embedding):
        """
        Test that the mock returns expected score value.

        Verifies:
        - Score matches mock's configured return value
        """
        result = product_similarity_threshold_svc(
            vector_query=sample_embedding,
            vector_db=mock_vector_db
        )

        # Mock returns 95.0 score
        assert result.score == 95.0
