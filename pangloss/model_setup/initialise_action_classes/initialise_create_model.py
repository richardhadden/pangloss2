from types import UnionType
from typing import Annotated, ClassVar, Literal, TypeVar, Union
from uuid import UUID

from pydantic import AnyHttpUrl, ConfigDict, Field, model_validator
from pydantic import create_model as pydantic_create_model
from pydantic.alias_generators import to_camel
from pydantic.fields import FieldInfo

from pangloss.model_setup.field_definitions import (
    RelationFieldDefinition,
    RelationToDocument,
    RelationToEntity,
)
from pangloss.model_setup.model_bases.base_object import _CreateBase, _DeclaredClass
from pangloss.model_setup.model_bases.conjunction import (
    Conjunction,
    _ConjunctionCreateBase,
)
from pangloss.model_setup.model_bases.document import Document, _DocumentCreateBase
from pangloss.model_setup.model_bases.embedded import Embedded
from pangloss.model_setup.model_bases.entity import Entity, _EntityCreateBase
from pangloss.model_setup.model_bases.reified_relation import (
    ReifiedRelation,
    ReifiedRelationDocument,
    _ReifiedRelationCreateBase,
    _ReifiedRelationDocumentCreateBase,
)
from pangloss.model_setup.model_bases.semantic_space import (
    SemanticSpace,
    _SemanticSpaceCreateBase,
)


def check_create_and_id_present(self):
    """Validator to ensure that both create_new=True and an ID must be provided together"""

    if getattr(self, "id", None) and not getattr(self, "create_new", None):
        raise ValueError(
            f"If an id is provided to {self.__class__.__name__}, the create_new=True flag must also be set"
        )
    if getattr(self, "create_new", None) and not getattr(self, "id", None):
        raise ValueError(
            f"If create_new=True flag set on {self.__class__.__name__}, an id must be provided"
        )
    return self


def get_model_validators(model):
    validators = {}
    if getattr(model._meta, "create_with_id", False):
        validators["check_create_and_id_present"] = model_validator(mode="after")(
            check_create_and_id_present
        )

    return validators


def build_id_field_on_create_model(model) -> None:
    assert model.Create
    if getattr(model._meta, "create_with_id", False):
        annotation = UUID | None
        if getattr(model._meta, "accept_url_as_id", False):
            annotation = UUID | AnyHttpUrl | None
        model.Create.model_fields["id"] = FieldInfo(annotation=annotation, default=None)
        model.Create.model_fields["create_new"] = FieldInfo(
            annotation=Literal[True] | None,  # pyright: ignore[reportArgumentType]
            default=None,  # pyright: ignore[reportArgumentType]
        )
        model.Create.model_rebuild()


def build_label_field_on_create_model(
    model: type[
        Document
        | Embedded
        | Entity
        | ReifiedRelation
        | ReifiedRelationDocument
        | Conjunction
        | SemanticSpace
    ],
):
    assert model.Create

    if getattr(model._meta, "require_label", True):
        model.Create.model_fields["label"] = FieldInfo(annotation=str)


def unpack_generic_fields(
    model: type[Document | Entity | ReifiedRelation],
) -> dict[str, TypeVar | type[list[TypeVar]]]:
    generic_fields = {}
    for f, fi in model.model_fields.items():
        if isinstance(fi.annotation, TypeVar):
            generic_fields[f] = fi.annotation

    return generic_fields


def can_have_create_model(model: type[_DeclaredClass]) -> bool:
    return issubclass(
        model,
        (
            Document,
            Entity,
            ReifiedRelation,
            ReifiedRelationDocument,
            Conjunction,
            SemanticSpace,
        ),
    )


def get_create_base_model_type(
    model: type[
        Document
        | Embedded
        | Entity
        | ReifiedRelation
        | ReifiedRelationDocument
        | Conjunction
        | SemanticSpace
    ],
) -> type[_CreateBase] | None:
    if issubclass(model, Document):
        return _DocumentCreateBase
    elif issubclass(model, Entity):
        return _EntityCreateBase
    elif issubclass(model, ReifiedRelation):
        return _ReifiedRelationCreateBase
    elif issubclass(model, ReifiedRelationDocument):
        return _ReifiedRelationDocumentCreateBase
    elif issubclass(model, Conjunction):
        return _ConjunctionCreateBase
    elif issubclass(model, SemanticSpace):
        return _SemanticSpaceCreateBase
    return None


def initialise_create_model(
    model: type[
        Document
        | Embedded
        | Entity
        | ReifiedRelation
        | ReifiedRelationDocument
        | Conjunction
        | SemanticSpace
    ],
) -> None:

    if not can_have_create_model(model):
        return

    # Checks if Create model has already been created; do not duplicate as we depend
    # on model reference!
    if "Create" in model.__dict__:
        return

    # Extracts from the _DeclaredClass definition the annotation for .Create
    create_base_type = get_create_base_model_type(model)
    if not create_base_type:
        return

    model.Create = pydantic_create_model(
        f"{model.__name__}Create",
        __base__=create_base_type,
        __validators__=get_model_validators(model),
        _owner=(ClassVar[model], model),
        __config__=ConfigDict(alias_generator=to_camel),
        type=(Literal[model.__name__], model.__name__),  # type: ignore
    )  # pyright: ignore[reportAttributeAccessIssue]

    build_id_field_on_create_model(model)
    build_label_field_on_create_model(model)

    model.Create.model_rebuild(force=True)


def get_relation_annotation_types(
    field_definition: RelationFieldDefinition,
) -> UnionType | type[list[UnionType]] | tuple[list[UnionType]]:
    types = []
    for type_option in field_definition.type_options:
        if isinstance(type_option, RelationToEntity):
            if type_option.edge_model:
                types.append(
                    type_option.annotated_type.ReferenceSet.apply_edge_model(
                        type_option.edge_model
                    )
                )
            else:
                types.append(type_option.annotated_type.ReferenceSet)
                if type_option.annotated_type._meta.create_inline:
                    types.append(type_option.annotated_type.Create)

        elif isinstance(type_option, RelationToDocument):
            if type_option.edge_model:
                types.append(
                    type_option.annotated_type.Create.apply_edge_model(
                        type_option.edge_model
                    )
                )
            else:
                types.append(type_option.annotated_type.Create)

    if not types:
        return None

    if field_definition.wrapper:
        return field_definition.wrapper[
            Annotated[Union[*types], Field(discriminator="type")]
        ]  # type: ignore
    return Union[*types]  # ty:ignore[invalid-type-form]


def add_fields_to_create_model(
    model: type[
        Document
        | Embedded
        | Entity
        | ReifiedRelation
        | ReifiedRelationDocument
        | Conjunction
        | SemanticSpace
    ],
) -> None:

    for field_name, field_definition in model._meta.fields.literal_fields.items():
        model.Create.model_fields[field_name] = FieldInfo(
            annotation=field_definition.annotated_type,
            validation_alias=to_camel(field_name),
            metadata=field_definition.validators,  # type: ignore
        )

    for field_name, field_definition in model._meta.fields.relation_fields.items():
        print(field_name)
        annotation = get_relation_annotation_types(field_definition)

        model.Create.model_fields[field_name] = FieldInfo(
            annotation=annotation,
            validation_alias=to_camel(field_name),
            metadata=field_definition.validators,  # type: ignore
            discriminator="type" if not field_definition.wrapper else None,
        )

    model.Create.model_rebuild(force=True)
