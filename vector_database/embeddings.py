from typing import Protocol
from langchain_openai import OpenAIEmbeddings
import structlog
import inspect
from .exceptions import EmbeddingsError

# 1. Setup structlog (simplified setup for key-value output)
structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.KeyValueRenderer(), # Renders to key=value pairs
    ]
)
# Get the base logger
base_logger = structlog.get_logger()

class Embeddor(Protocol):
    def embed_documents(self, documents: list[str]) -> list[list[float]] | None: 
        ...

class Embeddings:
    def __init__(self):
        self.client = OpenAIEmbeddings(
            model="text-embedding-3-small"
        )

    def embed_documents(self, documents: list[str]) -> list[list[float]] | None:
        scoped_logs = base_logger.bind(function_name=inspect.stack()[0][3], length_of_document=len(documents))

        try:
            embeddings = self.client.embed_documents(texts=documents)
            if not embeddings:
                scoped_logs.error("no embeddings returned")
                raise EmbeddingsError("No embeddings returned")

            scoped_logs = scoped_logs.bind(retrieved_embeddings=True)
            scoped_logs.info("Recieved Embeddings From Embeddings Models")

            return embeddings
        
        except Exception as e:
            scoped_logs.error(f"Failed to embed documents: {e}")
            return None
