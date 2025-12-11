import json
import random
import os
from dotenv import load_dotenv
import traceback

os.chdir("..")
load_dotenv()

from .embeddings import Embeddor, Embeddings

test_documents = {
    "test_1": {
        "description": "10 complete titles",
        "test": ["Tyler is a software engineer", "Sarah loves playing guitar", "The quick brown fox jumps over the lazy dog", "Machine learning transforms data into insights", "Coffee fuels productivity and creativity", "Python is a versatile programming language", "Mountains provide breathtaking views", "Reading books expands your knowledge", "Exercise improves both physical and mental health", "Music has the power to change moods"],
        "wanted_result": 10
    } 
}


class MockEmbeddor:
    def __init__(self):
        self.callback = 0

    def embed_documents(self, documents: list[str]) -> list[list[float]] | None:
        self.callback += 1
        embeds: list = []
        for document in documents:
            embeds.append([random.randint(-3, 3) for i in range (15)])

        return embeds
        

class UnitTests:
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

    def embed_documents(self):
        print("="*60)
        print(f"Testing -> {test_documents["test_1"]["description"]}")
        result = self.client.embed_documents(documents=test_documents["test_1"]["test"])
        print(f"Result: \n\n{result[:5]}")

    def embed_document_and_write_to_file(self):
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
            with open("vector_database/singe_document_embed.json", "w") as f:
                json.dump(file_content, f, indent=3)

            print("File written to successfully")

        except Exception as e:
            print(f"Error writing to file: {e} ->\n\n{traceback.format_exc()}")

if __name__ == "__main__":
    ut = UnitTests()
    it = IntegrationTest()
    it.embed_document_and_write_to_file()