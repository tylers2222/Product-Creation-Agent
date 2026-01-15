from typing import Type
from pydantic import BaseModel
from polyfactory.factories.pydantic_factory import ModelFactory

class MockLLM:
    """Mock LLM client that returns deterministic responses for testing."""

    def __init__(self):
        self.invoke_mini_call_count = 0
        self.invoke_max_call_count = 0

    def invoke_mini(self, system_query: str | None, user_query: str, response_schema: Type[BaseModel] | None = None) -> str | BaseModel:
        """Mock invoke_mini that returns a deterministic response."""
        self.invoke_mini_call_count += 1

        if response_schema:
            class FactoryResponse(ModelFactory):
                """Assisting the factories library"""
                __model__ = response_schema
            
            result = FactoryResponse.build()
            return result

        return '{"query": "Create a draft product", "extract_query": "Optimum Nutrition", "validated_data": {"variant": "test"}}'

    def invoke_max(self, system_query: str | None, user_query: str, response_schema: Type[BaseModel] | None = None) -> str | BaseModel:
        """Mock invoke_max that returns a deterministic response."""
        self.invoke_max_call_count += 1
        if response_schema:
            class FactoryResponse(ModelFactory):
                """Assisting the factories library"""
                __model__ = response_schema
            
            result = FactoryResponse.build()
            return result

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
