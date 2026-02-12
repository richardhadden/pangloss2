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

type BaseTypes = str | int | float | date | datetime
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
