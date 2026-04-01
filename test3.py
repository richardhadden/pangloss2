from typing import ClassVar

from pydantic import BaseModel


class A(BaseModel):
    thing: ClassVar[str]


print(A.__annotations_cache__)
