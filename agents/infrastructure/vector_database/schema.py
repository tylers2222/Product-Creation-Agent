from pydantic import BaseModel

class VectorFilter(BaseModel):
    """A filter for searching the vector database by payload"""
    key:    str
    value:  str

    def to_dict(self):
        return {self.key: self.value}