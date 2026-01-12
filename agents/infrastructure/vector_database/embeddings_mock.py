import random

class MockEmbeddor:
    def __init__(self):
        self.callback = 0

    def embed_documents(self, documents: list[str]) -> list[list[float]] | None:
        print("="*60)
        print("Called: MockedEmbeddor.embed_documents")
        self.callback += 1
        embeds: list = []
        for document in documents:
            embeds.append([random.randint(-3, 3) for i in range (15)])

        print("MockedEmbeddor.embed_documents returned embeds")
        return embeds