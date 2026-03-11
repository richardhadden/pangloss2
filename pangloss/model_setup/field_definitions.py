from dataclasses import dataclass
from dataclasses import field as dataclass_field
from typing import TYPE_CHECKING

from annotated_types import BaseMetadata
from pydantic.fields import FieldInfo

from pangloss.exceptions import PanglossInitialisationError
from pangloss.model_setup.model_bases.base_object import _DeclaredClass
from pangloss.model_setup.model_bases.base_types import BaseTypes

if TYPE_CHECKING:
    from pangloss.model_setup.model_bases.conjunction import Conjunction
    from pangloss.model_setup.model_bases.document import Document
    from pangloss.model_setup.model_bases.edge_model import EdgeModel
    from pangloss.model_setup.model_bases.entity import Entity
    from pangloss.model_setup.model_bases.reified_relation import (
        ReifiedRelation,
        ReifiedRelationDocument,
    )
    from pangloss.model_setup.model_bases.semantic_space import SemanticSpace


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


type TRelationFieldDefinitionAnnotation = (
    type[_DeclaredClass | BaseTypes | list]
    | type[list[type[_DeclaredClass | BaseTypes | list]]]
)


@dataclass(frozen=True, kw_only=True)
class RelationFieldDefinition(FieldDefinition):
    annotated_type: TRelationFieldDefinitionAnnotation
    type_options: set[RelationOption] = dataclass_field(default_factory=set)
    reverse_name: str
    overrides_parent_fields: list[str]
    wrapper: type[list | tuple] | None = None


@dataclass(frozen=True, kw_only=True)
class RelationOption:
    annotated_type: type
    edge_model: type[EdgeModel] | None = None


@dataclass(frozen=True, kw_only=True)
class RelationToDocument(RelationOption):
    annotated_type: type[Document]


@dataclass(frozen=True, kw_only=True)
class RelationToEntity(RelationOption):
    annotated_type: type["Entity"]


@dataclass(frozen=True, kw_only=True)
class RelationToSemanticspace(RelationOption):
    annotated_type: type["SemanticSpace"]


@dataclass(frozen=True, kw_only=True)
class RelationToConjunction(RelationOption):
    annotated_type: type["Conjunction"]


@dataclass(frozen=True, kw_only=True)
class RelationToReifiedRelation(RelationOption):
    annotated_type: type["ReifiedRelation"]


@dataclass(frozen=True, kw_only=True)
class RelationToReifiedRelationDocument(RelationOption):
    annotated_type: type["ReifiedRelationDocument"]


@dataclass
class ModelFields:
    fields: dict[str, FieldDefinition] = dataclass_field(default_factory=dict)

    def add_field(self, name: str, field_definition: FieldDefinition):

        self.fields[name] = field_definition
