import os
import sys

# Add parent directory to Python path so we can import sibling packages
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import logging
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_classic.agents import create_tool_calling_agent, AgentExecutor
from langchain_community.callbacks import get_openai_callback
from pydantic import BaseModel, Field
from shopify_api.client import DraftProduct
from agent.tools import web_scraper_and_similarity_searcher, product_drafter
from agent.schema import InvokeResponse
from agent.prompts import USER_PROMPT, SYSTEM_PROMPT
from agent.llm_client import llm

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

tools = [web_scraper_and_similarity_searcher, product_drafter]

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", USER_PROMPT),
    MessagesPlaceholder(variable_name="agent_scratchpad")
])

agent = create_tool_calling_agent(
    llm = llm,
    tools = tools,
    prompt = prompt
)

agent_executor = AgentExecutor(
    agent = agent,
    tools = tools,
    verbose = True,
    handle_parsing_errors = True
)

def invoke_agent(query: str) -> InvokeResponse | None:
    try:
        logger.info("invoking agent", extra={"query": query})

        with get_openai_callback() as cb:
            result = agent_executor.invoke({
                "input": query
            })

            if not result:
                logger.warning("agent returned no result", extra={"query": query})
                return None
            
            logger.info("agent invocation successful", extra={"query": query, "output": result.get("output", "")})
            return InvokeResponse(
                result = result,
                total_tokens = cb.total_tokens,
                total_cost = cb.total_cost
            )

    except Exception as e:
        logger.error("agent invocation failed", extra={"query": query, "error": str(e)}, exc_info=True)
        return None