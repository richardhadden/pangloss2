from dataclasses import dataclass
from dataclasses import field as dataclass_field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pangloss.model_setup.field_definitions import FieldDefinition


@dataclass
class ModelFields:
    fields: dict[str, FieldDefinition] = dataclass_field(default_factory=dict)

    def add_field(self, name: str, field_definition: FieldDefinition):

        self.fields[name] = field_definition
