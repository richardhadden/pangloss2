from dataclasses import dataclass
from dataclasses import field as dataclass_field

from pangloss.types import BaseTypes, CompositeTypes, ModelTypes


@dataclass(frozen=True)
class FieldDefinition:
    field_name: str
    annotated_type: BaseTypes | ModelTypes | CompositeTypes


@dataclass(frozen=True)
class LiteralFieldDefinition(FieldDefinition):
    pass


@dataclass
class ModelFields:
    fields: set[FieldDefinition] = dataclass_field(default_factory=set)
