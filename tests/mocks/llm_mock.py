from typing import Type
from pydantic import BaseModel
from polyfactory.factories.pydantic_factory import ModelFactory
from src.product_agent.models.llm_input import LLMInput

class MockLLM:
    """Mock LLM client that returns deterministic responses for testing."""

    def __init__(self):
        self.invoke_call_count = 0
        self.last_model_used = None

    async def invoke(self, llm_input: LLMInput) -> str | BaseModel:
        """
        Mock invoke that returns a deterministic response.

        Tracks which model was requested and returns appropriate test data.
        """
        self.invoke_call_count += 1
        self.last_model_used = llm_input.model

        if llm_input.response_schema:
            class FactoryResponse(ModelFactory):
                """Assisting the factories library"""
                __model__ = llm_input.response_schema

            result = FactoryResponse.build()
            return result

        # Return different responses based on model type for backward compatibility
        if llm_input.model == "mini_deterministic":
            return '{"query": "Create a draft product", "extract_query": "Optimum Nutrition", "validated_data": {"variant": "test"}}'

        # Default/max_deterministic response
        return '''{
    "title": "Test Product",
    "description": "<h2>Test Description</h2><p>This is a test product.</p>",
    "vendor": "Test Vendor",
    "type": "Test Category",
    "tags": ["test", "product", "mock"],
    "inventory": [1000, 1000],
    "lead_option": "Size",
    "baby_options": ["Flavour"],
    "variants": [
        {
            "option1_value": "5lbs",
            "option2_value": "Chocolate",
            "option3_value": null,
            "price": 50.00,
            "compare_at": 59.99,
            "product_weight": 2.27,
            "sku": 123456,
            "barcode": 789012
        }
    ]
}'''
