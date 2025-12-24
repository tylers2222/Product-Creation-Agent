import os
import random
import sys
import json
from pathlib import Path
import traceback
from unittest import registerResult

from dotenv import load_dotenv

# Add parent directory to Python path so we can import packages
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from agents.agent.agent_definitions import synthesis_agent
from agents.agent.tools import create_all_tools, ServiceContainer

from agents.infrastructure.vector_database.embeddings import Embeddings
from agents.infrastructure.vector_database.db import vector_database
from agents.infrastructure.firecrawl_api.client import FirecrawlClient
from agents.infrastructure.shopify_api.client import ShopifyClient

from agents.agent.agent import ShopifyProductWorkflow
from agents.agent.llm import llm_client
from qdrant_client.models import PointStruct

load_dotenv()


# Example 1: Same brand, but completely different category (Protein)
wrong_result_1 = PointStruct(
    id="6776123456789",
    vector=[0.45, 0.32, 0.18, 0.67, 0.21],  # Similar vector due to brand match
    payload={
        "title": "Optimum Nutrition Gold Standard 100% Whey",
        "body_html": "<h2>24g Protein per Serving</h2><p>The world's best-selling whey protein powder...</p>",
        "product_type": "Whey Protein",
        "tags": "Protein Powder, Whey, Sports Nutrition",
        "vendor": "Optimum Nutrition"
    }
)

# Example 2: Same brand, recovery/post-workout (not pre-workout)
wrong_result_2 = PointStruct(
    id="6776987654321",
    vector=[0.52, 0.28, 0.41, 0.63, 0.19],  # High similarity due to brand + workout keywords
    payload={
        "title": "Optimum Nutrition Glutamine Powder",
        "body_html": "<h2>Support Recovery</h2><p>5g of pure L-Glutamine for post-workout recovery and immune support...</p>",
        "product_type": "Amino Acids",
        "tags": "Recovery, Glutamine, Post-Workout, Sports Nutrition",
        "vendor": "Optimum Nutrition"
    }
)

# Example 3: Different brand, but has "nutrition" and "workout" keywords
wrong_result_3 = PointStruct(
    id="6776555444333",
    vector=[0.38, 0.44, 0.29, 0.71, 0.15],  # Moderate similarity from keyword overlap
    payload={
        "title": "MuscleTech Mass Gainer Nutrition Shake",
        "body_html": "<h2>1000 Calories Per Serving</h2><p>Premium mass gainer for post workout nutrition and muscle building...</p>",
        "product_type": "Mass Gainer",
        "tags": "Weight Gain, Mass Gainer, High Calorie, Post Workout Nutrition",
        "vendor": "MuscleTech"
    }
)

vector_result_list = {
    "search_result": [wrong_result_1, wrong_result_2, wrong_result_2]
}

class IntegrationTest:
    def __init__(self):
        self.sc = ServiceContainer(
            vector_db=vector_database(),
            embeddor=Embeddings(),
            scraper=FirecrawlClient(),
            shop=ShopifyClient(),
            llm=llm_client()
        )
        self.tools = create_all_tools(self.sc)

        self.agent = synthesis_agent(self.tools)
    def test_call_agent(self):
        print("="*60)
        print("STARTING test_call_agent")
        print(f"Service Container: {ServiceContainer is not None}")
        print(f"Tools: {self.tools}")
        print(f"Agent: {self.agent}")

        title = "Optimum Nutrition Pre Workout"
        query = f"Use tools to create a more relevant search in regards to {title}, our first go returned {vector_result_list}, return a list of json objects of the new return data if there was no return data can you relay the response object you got from the tool if you got a string that was an error message"

        print(f"Title: {title}")
        print(f"Query: {query}")

        print("Invoking Agent...")
        result = self.agent.invoke({"input": query})

        print(f"Type: {type(result)}")
        print(f"Result: \n\n{result}")

if __name__ == "__main__":
    it = IntegrationTest()
    it.test_call_agent()