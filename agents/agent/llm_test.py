import os
import sys
from dotenv import load_dotenv
from langchain_core.messages import AIMessage

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

load_dotenv()

from agents.agent.llm import markdown_summariser
from typing import Optional

class MockLLM:
    def __init__(self):
        pass

    def invoke_mini(self, system_query: Optional[str], user_query: str):
        # Return string directly to match the real llm_client behavior
        return """{"query": "Create a draft product", "extract_query": "Optimum Nutrition", "validated_data": {"variant": "tyler"}}"""

    def invoke_max(self, system_query: Optional[str], user_query: str):
        # Return string directly to match the real llm_client behavior
        # For fill_data, return a valid JSON structure for DraftProduct
        return """{
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
}"""


class unittest:
    def __init__(self):
        self.llm = MockLLM()

    def test_markdown_summariser(self):
        print("="*60)
        print("STARTING test_markdown_summariser")

        title = "Tyler"
        markdown = "fiownfionweiofniwnfioweangioenifgewnaciondsivneidngfiosdnfis"
        result = markdown_summariser(title=title, markdown=markdown, llm=self.llm)
        assert(result is not None)
        assert(result != "")
        print(f"Result: {result}")


if __name__ == "__main__":
    ut = unittest()
    ut.test_markdown_summariser()