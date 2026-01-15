import random

class MockEmbeddor:
    def __init__(self):
        self.callback = 0

    def embed_document(self, document: str) -> list[float]:
        """
        Mock single document embed

        In the mock we need to return distinguishable features so we can test different results

        If the legnth of the inpute document is > 15 we'll make the index 0 be negative

        And less than 15 the first index will be positive

        That way the vector db mock can use it to return different data based on the first index
        """
        if len(document) == 0:
            raise ValueError("Input document is empty")

        if len(document) > 15:
            result = [random.uniform(-5, -1)]
        else:
            result = [random.uniform(1, 5)]
        
        result.extend([random.uniform(-5, 5) for i in range(15)])
        return result

    def embed_documents(self, documents: list[str]) -> list[list[float]] | None:
        self.callback += 1
        embeds: list = []
        for document in documents:
            embeds.append([random.uniform(-3, 3) for i in range (15)])

        print("MockedEmbeddor.embed_documents returned embeds")
        return embeds