# Testing Guide

## Quick Start

```bash
# Run all unit tests (excludes integration tests)
pytest -m "not integration"

# Run all tests including integration
pytest

# Run tests in a specific directory
pytest agents/agent/

# Run a specific test file
pytest agents/agent/agent_test.py

# Run a specific test function
pytest agents/agent/agent_test.py::TestShopifyProductWorkflow::test_workflow_initialization
```

## Test Structure

```
├── conftest.py                          # Shared fixtures (mocks, sample data)
├── db/
│   └── client_test.py                   # Redis client tests
├── agents/
│   ├── agent/
│   │   ├── agent_test.py                # Workflow tests
│   │   ├── agent_definition_test.py     # Agent definition tests
│   │   ├── llm_test.py                  # LLM client tests
│   │   └── tools_test.py                # LangChain tools tests
│   └── infrastructure/
│       ├── firecrawl_api/
│       │   └── client_test.py           # Web scraper tests
│       ├── shopify_api/
│       │   ├── client_test.py           # Shopify API tests
│       │   └── product_schema_test.py   # Pydantic schema tests
│       └── vector_database/
│           ├── db_test.py               # Qdrant client tests
│           └── embeddings_test.py       # OpenAI embeddings tests
└── services/
    └── internal/
        └── vector_db_test.py            # Vector DB service tests
```

## Markers

### `@pytest.mark.integration`

Tests that hit real external services (Shopify, Qdrant, OpenAI, Firecrawl). These require environment variables to be set and may incur API costs.

```bash
# Run ONLY integration tests
pytest -m integration

# Run everything EXCEPT integration tests (default for CI)
pytest -m "not integration"
```

### `@pytest.mark.asyncio`

Tests for async functions. Requires `pytest-asyncio` plugin.

```bash
# These run automatically with pytest, no special flag needed
pytest agents/agent/agent_test.py
```

## Fixtures

All shared fixtures are defined in `conftest.py` at the project root.

### Mock Fixtures

| Fixture | Provides | Used For |
|---------|----------|----------|
| `mock_shop` | `MockShop` | Mocking Shopify API calls |
| `mock_scraper` | `MockScraperClient` | Mocking Firecrawl web scraping |
| `mock_vector_db` | `MockVectorDb` | Mocking Qdrant operations |
| `mock_embeddor` | `MockEmbeddor` | Mocking OpenAI embeddings |
| `mock_llm` | `MockLLM` | Mocking LLM responses |

### Sample Data Fixtures

| Fixture | Provides |
|---------|----------|
| `sample_variant` | Single product variant |
| `sample_draft_product` | Draft product with one option |
| `sample_draft_product_with_two_options` | Draft product with Size + Flavour |
| `sample_scored_points` | Vector search results |
| `sample_embedding` | 1536-dimension embedding vector |
| `sample_point_struct` | Qdrant PointStruct |
| `sample_documents_for_embedding` | List of product titles |
| `sample_shopify_product_data` | Raw Shopify product dicts |

### Using Fixtures

```python
def test_something(mock_shop, sample_draft_product):
    """Fixtures are injected by name."""
    result = mock_shop.make_a_product_draft(sample_draft_product)
    assert result is not None
```

## Common Commands

| Command | Description |
|---------|-------------|
| `pytest` | Run all tests |
| `pytest -v` | Verbose output (see test names) |
| `pytest -x` | Stop on first failure |
| `pytest -s` | Show print statements |
| `pytest --tb=short` | Shorter tracebacks |
| `pytest -k "vector"` | Run tests with "vector" in name |
| `pytest --collect-only` | List tests without running |
| `pytest --lf` | Run only last failed tests |
| `pytest -n auto` | Run tests in parallel (requires pytest-xdist) |

## Running Tests for a Specific Module

When working on a specific file, run its associated tests:

```bash
# Working on agents/agent/agent.py
pytest agents/agent/agent_test.py -v

# Working on infrastructure clients
pytest agents/infrastructure/shopify_api/client_test.py -v

# Working on services
pytest services/internal/vector_db_test.py -v
```

## Environment Variables for Integration Tests

Integration tests require these environment variables:

```bash
# Shopify
SHOPIFY_API_KEY=xxx
SHOPIFY_API_SECRET=xxx
SHOPIFY_TOKEN=xxx
SHOP_NAME=xxx
SHOP_URL=xxx
LOCATION_ONE_ID=xxx
LOCATION_TWO_ID=xxx

# Qdrant
QDRANT_URL=xxx
QDRANT_API_KEY=xxx

# OpenAI
OPENAI_API_KEY=xxx

# Firecrawl
FIRECRAWL_API_KEY=xxx
```

## Writing New Tests

### TestCase Pattern (Recommended)

We use a standardized `TestCase` pattern that bundles input data with expected results. This makes tests self-documenting and easier to maintain.

**TestCase Structure:**
```python
TestCase(
    description="What this test verifies",
    data={...},      # Input data for the function
    expected={...}   # Expected results to assert against
)
```

**Available TestCase Fixtures:**

| Fixture | Tests |
|---------|-------|
| `tc_query_extract` | Query extraction service |
| `tc_check_product_exists_found_by_sku` | Product exists via SKU match |
| `tc_check_product_exists_found_by_vector` | Product exists via vector similarity |
| `tc_check_product_exists_not_found` | Product does not exist |
| `tc_similarity_search` | Vector similarity search |
| `tc_markdown_summariser` | Markdown summarisation |

**Using TestCase in Tests:**

```python
def test_query_extract(self, workflow, tc_query_extract):
    """Test query extraction with TestCase pattern."""
    tc = tc_query_extract

    # Call function with test data
    result = workflow.query_extract(
        request_id=tc.data["request_id"],
        query=tc.data["query"]
    )

    # Assert against expected results
    assert isinstance(result, tc.expected["type"])
    assert result.field == tc.expected["field_value"]
```

**Creating New TestCase Fixtures:**

Add to `conftest.py`:

```python
@pytest.fixture
def tc_my_new_test():
    """Test case for my_function."""
    return TestCase(
        description="Should do X when given Y",
        data={
            "input_field": "value",
            "other_input": SomeModel(...)
        },
        expected={
            "type": ExpectedReturnType,
            "field_value": "expected",
            "should_be_none": False
        }
    )
```

### Unit Test Pattern

```python
class TestMyFeature:
    """Unit tests using mocks."""

    def test_happy_path(self, mock_shop, tc_my_test):
        """Test the expected behavior using TestCase."""
        tc = tc_my_test

        result = my_function(mock_shop, tc.data["input"])

        assert isinstance(result, tc.expected["type"])
        assert result.status == tc.expected["status"]

    def test_edge_case(self, mock_shop):
        """Test edge cases."""
        result = my_function(mock_shop, None)
        assert result is None
```

### Integration Test Pattern

```python
@pytest.mark.integration
class TestMyFeatureIntegration:
    """Integration tests hitting real services."""

    def test_real_api_call(self, tc_my_test):
        """Test with real external service."""
        from config import create_service_container
        sc = create_service_container()
        tc = tc_my_test

        result = my_function(sc.shop, tc.data["input"])

        assert result is not None
        assert isinstance(result, tc.expected["type"])
```

## Troubleshooting

### ModuleNotFoundError

If you see `ModuleNotFoundError: No module named 'xxx'`:

1. Make sure you're running from the project root
2. Check that all directories have `__init__.py`
3. Activate your virtual environment: `source .venv/bin/activate`

### Tests Not Collected

If tests aren't being found:

1. Ensure test files end with `_test.py`
2. Ensure test functions start with `test_`
3. Check for syntax errors: `python -m py_compile path/to/test_file.py`

### Integration Tests Failing

1. Check environment variables are set
2. Verify API keys are valid
3. Check network connectivity
4. Review rate limits on external services
