from typing import Protocol
from langchain_openai import OpenAIEmbeddings
from langgraph.store.base import embed
import structlog
import inspect
from .exceptions import EmbeddingsError

logger = structlog.get_logger(__name__)

class Embeddor(Protocol):
    def embed_document(self, document: str) -> list[float]:
        ...

    def embed_documents(self, documents: list[str]) -> list[list[float]] | None: 
        ...

class Embeddings:
    def __init__(self, api_key: str):
        self.client = OpenAIEmbeddings(
            model="text-embedding-3-small",
            api_key=api_key
        )

    def embed_document(self, document: str) -> list[float]:
        """Single embed function"""
        logger.debug("Starting embed_document", document=document)
        if document == "":
            raise ValueError("Input document is empty")

        return_embed = self.client.embed_query(text=document)
        
        logger.info("Successfully Recieved Embeddings From Single Embeddings Models")
        return return_embed

    def embed_documents(self, documents: list[str]) -> list[list[float]] | None:
        """Multiple embed function"""
        logger.debug("Starting embed_documents", documents=documents[:15])

        try:
            embeddings = self.client.embed_documents(texts=documents)
            if not embeddings:
                logger.error("no embeddings returned from documents", length_of_documents=len(documents))
                raise EmbeddingsError("No embeddings returned")

            logger.info("Successfully Recieved Embeddings From Multi Embeddings Models")
            return embeddings
        
        except Exception as e:
            logger.error("Failed to embed documents", error=e, documents=documents)
            return None
