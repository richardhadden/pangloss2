from typing import TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:
    from pangloss.model_setup.model_bases.document import Document
    from pangloss.model_setup.model_bases.edge_model import EdgeModel
    from pangloss.model_setup.model_bases.entity import Entity
from pangloss.model_setup.model_bases.sub_document import SubDocument


class FulFils[T]:
    pass


class ViaEdge[Target: Entity | Document | SubDocument, Model: EdgeModel](BaseModel):
    pass


class AnnotatedLiteral[LiteralType](BaseModel):
    value: LiteralType
