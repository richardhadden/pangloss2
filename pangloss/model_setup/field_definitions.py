from dataclasses import dataclass
from datetime import date, datetime

from pangloss.models import (
    Document,
    Entity,
    HeritableTrait,
    NonHeritableTrait,
    ReifiedRelation,
    ReifiedRelationDocument,
    SubDocument,
)

type BaseTypes = type[str | int | float | date | datetime]
type ModelTypes = type[
    Document
    | SubDocument
    | Entity
    | HeritableTrait
    | NonHeritableTrait
    | ReifiedRelation
    | ReifiedRelationDocument
]
type CompositeTypes = type[list[BaseTypes | ModelTypes]]


@dataclass(frozen=True)
class FieldDefinition:
    field_name: str
    annotated_type: BaseTypes | ModelTypes | CompositeTypes


@dataclass(frozen=True)
class LiteralFieldDefinition(FieldDefinition):
    pass
