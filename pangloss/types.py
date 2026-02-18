from pangloss.model_setup.model_bases.base_types import BaseTypes
from pangloss.models import (
    Document,
    Entity,
    HeritableTrait,
    NonHeritableTrait,
    ReifiedRelation,
    ReifiedRelationDocument,
    SubDocument,
)

type ModelTypes = (
    Document
    | SubDocument
    | Entity
    | HeritableTrait
    | NonHeritableTrait
    | ReifiedRelation
    | ReifiedRelationDocument
)
type CompositeTypes = list[type[BaseTypes] | type[ModelTypes]]
