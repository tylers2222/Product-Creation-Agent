import pytest


# -----------------------------------------------------------------------------
# Test Data Fixtures
# -----------------------------------------------------------------------------

@pytest.fixture
def sample_documents():
    """Fixture providing sample documents for embedding."""
    return [
        "Tyler",
        "Tyler is a software engineer",
        "Sarah loves playing guitar",
        "Machine learning transforms data into insights",
        "Coffee fuels productivity and creativity",
        "Python is a versatile programming language",
    ]


# -----------------------------------------------------------------------------
# Unit Tests
# -----------------------------------------------------------------------------

class TestMockEmbeddor:
    """Unit tests for MockEmbeddor client."""

    def test_single_embed_positive_first_integer(self, mock_embeddor, sample_documents):
        """ 
        Test that returns the first index of an embedding as positive
        giving us flexibility in vector db searches when mocked
        """
        for document in sample_documents:
            if len(document) < 15:
                under_15_char_document = document
                break

        positive_first_integer_embed = mock_embeddor.embed_document(document=under_15_char_document)
        assert positive_first_integer_embed is not None
        assert positive_first_integer_embed[0] > 0

    def test_single_embed_negative_first_integer(self, mock_embeddor, sample_documents):
        """ 
        Test that returns the first index of an embedding as negative
        giving us flexibility in vector db searches when mocked
        """

        for document in sample_documents:
            if len(document) > 15:
                over_15_char_document = document
                break

        negative_first_integer_embed = mock_embeddor.embed_document(document=over_15_char_document)
        assert negative_first_integer_embed is not None
        assert negative_first_integer_embed[0] < 0

    def test_value_error(self, mock_embeddor, sample_documents):
        with pytest.raises(ValueError):
            mock_embeddor.embed_document(document="")

    def test_embed_documents_returns_list(self, mock_embeddor, sample_documents):
        """Test that embed_documents returns a list of embeddings."""
        result = mock_embeddor.embed_documents(documents=sample_documents)

        assert result is not None
        assert isinstance(result, list)

    def test_embed_documents_returns_correct_count(self, mock_embeddor, sample_documents):
        """Test that embed_documents returns the correct number of embeddings."""
        result = mock_embeddor.embed_documents(documents=sample_documents)

        assert len(result) == len(sample_documents)

    def test_embed_documents_returns_vectors(self, mock_embeddor, sample_documents):
        """Test that each embedding is a list of floats."""
        result = mock_embeddor.embed_documents(documents=sample_documents)

        for embedding in result:
            assert isinstance(embedding, list)
            assert len(embedding) > 0

    def test_embed_single_document(self, mock_embeddor):
        """Test embedding a single document."""
        result = mock_embeddor.embed_documents(["Test document"])

        assert result is not None
        assert len(result) == 1

    def test_embed_empty_list(self, mock_embeddor):
        """Test embedding an empty list."""
        result = mock_embeddor.embed_documents([])

        assert result is not None
        assert len(result) == 0


# -----------------------------------------------------------------------------
# Integration Tests
# -----------------------------------------------------------------------------

@pytest.mark.integration
class TestEmbeddingsIntegration:
    """Integration tests using real OpenAI API.

    These tests require OPENAI_API_KEY to be set.

    Run with: pytest -m integration
    """

    @pytest.fixture
    def real_embeddor(self):
        """Create a real OpenAI embeddings client."""
        from product_agent.infrastructure.vector_db.embeddings import Embeddings
        return Embeddings()

    def test_embed_documents_returns_embeddings(self, real_embeddor, sample_documents):
        """Test that real embedding returns correct number of vectors."""
        result = real_embeddor.embed_documents(documents=sample_documents)

        assert result is not None
        assert len(result) == len(sample_documents)

    def test_embeddings_have_correct_dimensions(self, real_embeddor):
        """Test that embeddings have the expected dimensions (1536 for text-embedding-3-small)."""
        result = real_embeddor.embed_documents(["Test document"])

        assert result is not None
        assert len(result) == 1
        # text-embedding-3-small produces 1536-dimension vectors
        assert len(result[0]) == 1536

    def test_embeddings_are_floats(self, real_embeddor):
        """Test that embedding values are floats."""
        result = real_embeddor.embed_documents(["Test document"])

        assert result is not None
        for value in result[0][:10]:  # Check first 10 values
            assert isinstance(value, float)
