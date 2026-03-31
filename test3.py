from typing import Annotated

from annotated_types import MaxLen
from pydantic import BaseModel


class A(BaseModel):
    thing: Annotated[str, MaxLen(1)]


print(A.model_fields["thing"])
