"""
Agent Builders - Factory functions for constructing agents.

This module builds fully-configured agents by combining:
- Agent definitions (prompts, models) from agents/definitions/
- Tools built with dependencies from ServiceContainer
- LangChain/LangGraph infrastructure
"""
from langchain_core.language_models.llms import aget_prompts
import structlog
from langchain_classic.agents import create_tool_calling_agent, AgentExecutor
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from agents.definitions.synthesis import AgentConfig
from .container import ServiceContainer
from services.internal.vector_db import similarity_search_svc
from services.internal.embeddor import embed_search_svc
from langchain.tools import tool

logger = structlog.get_logger(__name__)


def _build_similarity_tool(container: ServiceContainer):
    """
    Build the get_similar_products tool with injected dependencies.

    This tool allows agents to query the vector database for similar products.
    """
    @tool
    def get_similar_products(query: str):
        """
        Search the vector database for products similar to the query.

        Use this when the current similar products don't match the target category.
        Use generic category names, not brand names.

        Args:
            query: Product category to search for (e.g., "pre-workout supplement")

        Returns:
            List of similar products from the store's catalog
        """
        query_embedded = embed_search_svc(query=query, embeddings=container.embeddor)
        if query_embedded is None:
            return "Failed to embed the query"

        similar_products = similarity_search_svc(
            vector_query=query_embedded,
            results_wanted=5,
            vector_db=container.vector_db
        )
        if similar_products is None:
            return "Failed to fetch similar products from database"

        result = [p.payload for p in similar_products if p.payload]
        logger.debug("get_similar_products tool result", count=len(result))
        return result

    return get_similar_products


def build_synthesis_agent(container: ServiceContainer,
        config_settings: AgentConfig) -> AgentExecutor:
    """
    Build the synthesis agent for evaluating vector search relevance.

    This agent:
    - Analyzes similar products returned from vector search
    - Calculates relevance scores
    - Requeries with better search terms if relevance is low

    Args:
        container: ServiceContainer with vector_db and embeddor dependencies

    Returns:
        Configured AgentExecutor ready to invoke
    """
    logger.debug("Building synthesis agent", config=config_settings.name)

    tools = [_build_similarity_tool(container)]

    prompt = ChatPromptTemplate.from_messages([
        ("system", config_settings.prompt),
        ("human", "{input}"),
        MessagesPlaceholder("agent_scratchpad"),
    ])

    llm = ChatOpenAI(
        model=config_settings.model,
        temperature=config_settings.temperature
    )

    agent = create_tool_calling_agent(
        llm=llm,
        tools=tools,
        prompt=prompt
    )

    logger.info("Built synthesis agent", model=config_settings.model)
    return AgentExecutor(agent=agent, tools=tools, verbose=False)


def build_all_tools(container: ServiceContainer) -> list:
    """
    Build all tools that agents might need.

    Returns a list of tools for use in workflows that need
    tool access outside of specific agents.

    Args:
        container: ServiceContainer with all dependencies

    Returns:
        List of LangChain tools
    """
    return [_build_similarity_tool(container)]
