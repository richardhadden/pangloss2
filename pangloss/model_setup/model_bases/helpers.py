from typing import TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:
    from pangloss.model_setup.model_bases.edge_model import EdgeModel


class Fulfils[T](BaseModel):
    pass


class ViaEdge[Target, Model: EdgeModel](BaseModel):
    """There is clearly a problem with this; in type checking, Model must be type[EdgeModel],
    but genericlaly subclassing with real EdgeModel subclass goes all wrong"""

    pass


class AnnotatedLiteral[LiteralType](BaseModel):
    value: LiteralType
