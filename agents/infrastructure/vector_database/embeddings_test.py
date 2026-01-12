import json
import random
import os
import sys
from dotenv import load_dotenv
import traceback

# Add parent directory to Python path so we can import packages
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from agents.infrastructure.vector_database.embeddings import Embeddor, Embeddings
from agents.infrastructure.vector_database.embeddings_mock import MockEmbeddor

os.chdir("..")
load_dotenv()

test_documents = {
    "test_1": {
        "description": "10 complete titles",
        "test": ["Tyler is a software engineer", "Sarah loves playing guitar", "The quick brown fox jumps over the lazy dog", "Machine learning transforms data into insights", "Coffee fuels productivity and creativity", "Python is a versatile programming language", "Mountains provide breathtaking views", "Reading books expands your knowledge", "Exercise improves both physical and mental health", "Music has the power to change moods"],
        "wanted_result": 10
    } 
}       

class UnitTests:
    """Unit tests for the embeddings package"""
    def __init__(self) -> None:
        self.embeddor: Embeddor = MockEmbeddor()

    def embed_documents(self):
        for key, value in test_documents.items():
            print("="*60)
            print(f"Testing -> {value["description"]}")
            result = self.embeddor.embed_documents(documents=value["test"])
            print(f"Length Of Result: {len(result)}")
            assert(len(result) == value["wanted_result"])

class IntegrationTest:
    def __init__(self) -> None:
        self.client: Embeddor = Embeddings()

    def test_embed_documents(self):
        print("="*60)
        print(f"Testing -> {test_documents["test_1"]["description"]}")
        result = self.client.embed_documents(documents=test_documents["test_1"]["test"])
        print(f"Result: \n\n{result[:5]}")

    def test_embed_document_and_write_to_file(self):
        """A helping testing to assist searching in the database test script"""
        print("="*60)
        print("Testing -> Writing a real embed to file")

        document = "Optimum Nutrition Whey Protein Powder"

        result = self.client.embed_documents(documents=[document])
        assert(result is not None)

        file_content = {
            "text": document,
            "embed": result[0]
        }

        try:
            with open("vector_database/singe_document_embed.json", "w", encoding="utf-8") as f:
                json.dump(file_content, f, indent=3)

            print("File written to successfully")

        except Exception as e:
            print(f"Error writing to file: {e} ->\n\n{traceback.format_exc()}")
    
    def test_embedding_some_product_names(self):
        products = ["Ultra Pure Creatine", "Creatine +", "Micronized Creatine"]
        embed_result = self.client.embed_documents(products)

        final_json_result = {}
        for idx, embed in enumerate(embed_result):
            product = products[idx]
            print(f"Adding {product} to result")
            final_json_result[product] = embed

        path = "vector_database/product_names_embedded.json"
        with open(path, "w") as f:
            json.dump(final_json_result, f, indent=3)
            print(f"Written file to path: {path}")


if __name__ == "__main__":
    ut = UnitTests()
    it = IntegrationTest()
    #it.test_embed_document_and_write_to_file()
    it.test_embedding_some_product_names()