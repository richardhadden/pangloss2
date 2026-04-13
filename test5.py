from pydantic import BaseModel


class A(BaseModel):
    name: str


class B(BaseModel):
    name: str


a = A(name="hello")
B(**a.model_dump())
