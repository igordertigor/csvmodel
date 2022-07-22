from pydantic import BaseModel


class ExampleModel(BaseModel):
    col1: int
    col2: str
    col3: float
