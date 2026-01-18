from pydantic import BaseModel
from polyfactory.factories.pydantic_factory import ModelFactory

class MockSynthesisAgent:
    def __init__(self):
        pass

    def invoke(self, query: str, model: BaseModel | None = None):
        if len(query) > 10:
            class Filled(ModelFactory):
                __model__ = model

            return Filled.build()

        return query