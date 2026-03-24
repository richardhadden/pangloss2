from pangloss.model_setup.model_bases.base_types import BaseTypes
from pangloss.models import (
    Document,
    Entity,
    NonHeritableTrait,
    ReifiedRelation,
    ReifiedRelationDocument,
    Trait,
)

type ModelTypes = (
    Document
    | Entity
    | Trait
    | NonHeritableTrait
    | ReifiedRelation
    | ReifiedRelationDocument
)
type CompositeTypes = list[type[BaseTypes] | type[ModelTypes]]
