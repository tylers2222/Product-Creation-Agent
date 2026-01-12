from typing import Protocol
from langchain_openai import OpenAIEmbeddings
import structlog
import inspect
from .exceptions import EmbeddingsError

logger = structlog.get_logger(__name__)

class Embeddor(Protocol):
    def embed_documents(self, documents: list[str]) -> list[list[float]] | None: 
        ...

class Embeddings:
    def __init__(self):
        self.client = OpenAIEmbeddings(
            model="text-embedding-3-small"
        )

    def embed_documents(self, documents: list[str]) -> list[list[float]] | None:
        logger.debug("Starting embed_documents", documents=documents[:15])

        try:
            embeddings = self.client.embed_documents(texts=documents)
            if not embeddings:
                logger.error("no embeddings returned from documents", length_of_documents=len(documents))
                raise EmbeddingsError("No embeddings returned")

            logger.info("Successfully Recieved Embeddings From Embeddings Models")
            return embeddings
        
        except Exception as e:
            logger.error("Failed to embed documents", error=e, documents=documents)
            return None
