from typing import TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:
    from pangloss.model_setup.model_bases.edge_model import EdgeModel


class FulFils[T]:
    pass


class ViaEdge[Target, Model: EdgeModel](BaseModel):
    pass


class AnnotatedLiteral[LiteralType](BaseModel):
    value: LiteralType
