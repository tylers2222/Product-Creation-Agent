"""
Agent Builders - Factory functions for constructing agents.

This module builds fully-configured agents by combining:
- Agent definitions (prompts, models) from agents/definitions/
- Tools built with dependencies from ServiceContainer
- LangChain/LangGraph infrastructure
"""
import structlog
from langchain_classic.agents import create_tool_calling_agent, AgentExecutor
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from .config import AgentConfig
from ..container import ServiceContainer
from product_agent.services.infrastructure.vector_search import similarity_search_svc
from product_agent.services.infrastructure.embedding import embed_search_svc

from product_agent.tools.similarity import build_similar_products_tool

logger = structlog.get_logger(__name__)

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

    prompt = ChatPromptTemplate.from_messages([
        ("system", config_settings.system_prompt),
        ("human", "{input}"),
        MessagesPlaceholder("agent_scratchpad"),
    ])

    llm = ChatOpenAI(
        model=config_settings.model,
        temperature=config_settings.temperature
    )

    tools = build_similar_products_tool(container.embeddor, container.vector_db),

    agent = create_tool_calling_agent(
        llm=llm,
        tools=tools,
        prompt=prompt
    )

    logger.info("Built synthesis agent", model=config_settings.model)
    return AgentExecutor(agent=agent, tools=tools, verbose=False)
