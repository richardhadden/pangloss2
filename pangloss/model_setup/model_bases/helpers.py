from typing import TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:
    from pangloss.model_setup.model_bases.edge_model import EdgeModel
    from pangloss.model_setup.model_bases.entity import Entity


class FulFils[T]:
    pass


class ViaEdge[Target: Entity, Model: EdgeModel]:
    pass


class AnnotatedLiteral[LiteralType](BaseModel):
    value: LiteralType
