from pydantic import BaseModel
import pytest

from product_agent.services.orchestrators.content_extraction import analyse_markdowns_with_llm_svc

class TestOrchestrators:
    """Testing service orchestrators"""
    @pytest.mark.asyncio
    async def test_markdowns_to_synthesis(self, mock_llm):
        """Testing markdowns getting synthesised"""
        markdowns = [
            "fsdabnfuasbnfasdfas",
            "fsdabnfuasbnfasdffsfasf",
            "fsdabnfuasbnf"
        ]
        result = await analyse_markdowns_with_llm_svc(
            markdowns=markdowns, 
            llm=mock_llm, model="scraper_mini")

        assert result is not None
        print(type(result))
        assert isinstance(result, BaseModel)

        result_dict = result.model_dump()
        for key, value in result_dict.items():
            print()
            print("Key: ", key)
            print("Value: ", value)