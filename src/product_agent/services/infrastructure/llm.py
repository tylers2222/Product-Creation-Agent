from product_agent.infrastructure.llm.client import LLM
from product_agent.models.llm_input import LLMInput

async def llm_service(llm_input: LLMInput, llm: LLM):
    """A service layer impl of llms invoke"""
    return await llm.invoke(llm_input)