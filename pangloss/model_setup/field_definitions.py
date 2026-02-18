from dataclasses import dataclass
from dataclasses import field as dataclass_field

from annotated_types import BaseMetadata
from pydantic.fields import FieldInfo

from pangloss.exceptions import PanglossInitialisationError
from pangloss.model_setup.model_bases.base_object import _DeclaredClass
from pangloss.model_setup.model_bases.base_types import BaseTypes


@dataclass(frozen=True, kw_only=True)
class FieldDefinition:
    field_on_model: type[_DeclaredClass]
    field_name: str
    annotated_type: type[_DeclaredClass | BaseTypes | list]

    @property
    def model_field(self) -> FieldInfo:
        try:
            return self.field_on_model.model_fields[self.field_name]
        except KeyError:
            raise PanglossInitialisationError(
                f"FieldInfo object for field {self.field_name} on model {self.field_on_model.__name__} not found"
            )
        except Exception:
            raise PanglossInitialisationError("Model Config not accessible yet")


@dataclass(frozen=True, kw_only=True)
class LiteralFieldDefinition(FieldDefinition):
    annotated_type: type[BaseTypes]
    validators: list[BaseMetadata] = dataclass_field(default_factory=list)


@dataclass(frozen=True, kw_only=True)
class ListFieldDefinition(FieldDefinition):
    annotated_type: type[list[BaseTypes]]
    validators: list[type[BaseMetadata]] = dataclass_field(default_factory=list)
    inner_type: type[BaseTypes]
    inner_type_validators: list[BaseMetadata] = dataclass_field(default_factory=list)


@dataclass
class ModelFields:
    fields: dict[str, FieldDefinition] = dataclass_field(default_factory=dict)

    def add_field(self, name: str, field_definition: FieldDefinition):
        self.fields[name] = field_definition
