from typing import Optional, Protocol
from langchain_openai import ChatOpenAI
from .prompts import markdown_summariser_prompt, mardown_summariser_system_prompt

class LLMError(Exception):
    pass

class LLM(Protocol):
    def invoke_mini(self, system_query: Optional[str], user_query: str):
        ...

    def invoke_max(self, system_query: Optional[str], user_query: str):
        ...

class llm_client:
    def __init__(self):
        self.llm_mini_deterministic = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.1
        )

        self.llm_max_deterministic = ChatOpenAI(
            model="gpt-4o",
            temperature=0.1
        )

    def invoke_mini(self, system_query: Optional[str], user_query: str) -> str:
        invocation: list[dict] = []
        if system_query is not None:
            invocation.append({"role": "system", "content": system_query})

        invocation.append({"role": "user", "content": user_query})

        result = self.llm_mini_deterministic.invoke(invocation)
        if result is None:
            raise LLMError("No result returned from LLM")

        return result.content

    def invoke_max(self, system_query: Optional[str], user_query: str) -> str:
        invocation: list[dict] = []
        if system_query is not None:
            invocation.append({"role": "system", "content": system_query})

        invocation.append({"role": "user", "content": user_query})

        result = self.llm_max_deterministic.invoke(invocation)
        if result is None:
            raise LLMError("No result returned from LLM")

        return result.content


def markdown_summariser(title: str, markdown: str, llm: LLM):
    """Title: what we want to find in the markdown, Markdown is the str we want to find it in"""
    user_query = markdown_summariser_prompt(title=title, markdown=markdown)
    response = llm.invoke_mini(system_query=mardown_summariser_system_prompt, user_query=user_query)
    return response  # invoke_mini already returns a string