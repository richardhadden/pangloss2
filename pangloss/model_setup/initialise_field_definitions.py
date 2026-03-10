from datetime import date, datetime
from inspect import isclass
from types import UnionType
from typing import TYPE_CHECKING, Annotated, Any, TypeIs, Union, get_args, get_origin

from annotated_types import BaseMetadata
from pydantic._internal._generics import PydanticGenericMetadata
from pydantic.fields import FieldInfo

from pangloss.exceptions import PanglossModelError
from pangloss.model_setup.field_definitions import (
    ListFieldDefinition,
    LiteralFieldDefinition,
    RelationFieldDefinition,
)
from pangloss.model_setup.model_bases.edge_model import EdgeModel
from pangloss.model_setup.model_bases.helpers import ViaEdge

if TYPE_CHECKING:
    from pangloss.model_setup.model_bases.base_object import _DeclaredClass
    from pangloss.model_setup.model_bases.document import Document
    from pangloss.model_setup.model_bases.entity import Entity


LITERAL_TYPES = {str, int, float, date, datetime}

type LiteralTypes = str | int | float | date | datetime


def is_literal(
    annotation: type[Any] | None,
) -> TypeIs[type[str | int | float | date | datetime]]:
    """Checks whether an annotation is of a literal type"""
    return annotation in LITERAL_TYPES


def is_list_of_literal(
    annotation: type[Any] | None,
) -> TypeIs[type[list[str | int | float | date | datetime]]]:

    # list[X]
    if get_origin(annotation) is not list:
        return False
    # (X,)
    args = get_args(annotation)
    if not args:
        return False

    inner_type = args[0]

    if is_literal(inner_type):
        return True

    if get_origin(inner_type) is Annotated:
        inner_type_args = get_args(inner_type)
        if not inner_type_args:
            return False
        if is_literal(inner_type_args[0]):
            return True
    return False


def is_union_of_relatable(
    annotation: type[Any] | None | UnionType,
) -> TypeIs[type[Union[Document, Entity]]]:
    if isinstance(annotation, UnionType):
        return all(is_relatable(arg) for arg in get_args(annotation))
    return False


def is_via_edge(
    annotation: type[Any] | None | UnionType,
) -> TypeIs[type[ViaEdge[Document | Entity, EdgeModel]]]:
    generic_metadata: PydanticGenericMetadata | None = getattr(
        annotation, "__pydantic_generic_metadata__", None
    )
    if generic_metadata and generic_metadata["origin"] is ViaEdge:
        if is_relatable(generic_metadata["args"][0]):
            return True
    return False


def is_relatable(
    annotation: type[Any] | None | UnionType,
) -> TypeIs[type[Document | Entity] | type[Union[Document, Entity]]]:
    from pangloss.model_setup.model_bases.document import Document
    from pangloss.model_setup.model_bases.entity import Entity

    if is_union_of_relatable(annotation):
        return True

    if is_via_edge(annotation):
        return True

    if isclass(annotation) and issubclass(annotation, (Document, Entity)):
        return True
    return False


def is_list_relatable(annotation: type[Any] | None):

    # list[X]
    if get_origin(annotation) is not list:
        return False
    # (X,)
    args = get_args(annotation)
    if not args:
        return False

    inner_type = args[0]

    if is_relatable(inner_type):
        return True

    if get_origin(inner_type) is Annotated:
        inner_type_args = get_args(inner_type)
        if not inner_type_args:
            return False
        if is_relatable(inner_type_args[0]):
            return True
    return False


def build_list_field_definition(
    field_name: str, field_info: FieldInfo, model: type[_DeclaredClass]
) -> ListFieldDefinition:
    try:
        assert field_info.annotation
        list_inner_type_tuple: tuple[Any, ...] = get_args(field_info.annotation)
        assert list_inner_type_tuple
        list_inner_type: Any = list_inner_type_tuple[0]

        inner_type_validators: list[BaseMetadata] = []
        if get_origin(list_inner_type) is Annotated:
            annotated_inner_type_tuple: tuple[Any, ...] = get_args(list_inner_type)
            assert annotated_inner_type_tuple
            list_inner_type = annotated_inner_type_tuple[0]
            inner_type_validators: list[BaseMetadata] = [
                arg
                for arg in annotated_inner_type_tuple
                if isinstance(arg, BaseMetadata)
            ]
        assert is_literal(list_inner_type)
        return ListFieldDefinition(
            field_on_model=model,
            field_name=field_name,
            annotated_type=field_info.annotation,
            validators=field_info.metadata,
            inner_type=list_inner_type,
            inner_type_validators=inner_type_validators,
        )
    except AssertionError:
        raise PanglossModelError(
            f"{model.__name__}.{field_name} has an invalid list field definition"
        )


def build_relatable_field_definition(
    field_name: str, field_info: FieldInfo, model: type[_DeclaredClass]
) -> RelationFieldDefinition:
    if (
        is_relatable(field_info.annotation)
        and not is_union_of_relatable(field_info.annotation)
        and not is_via_edge(field_info.annotation)
    ):
        return RelationFieldDefinition(
            field_name=field_name,
            field_on_model=model,
            annotated_type=field_info.annotation,
            type_options=[],
            overrides_parent_fields=[],
            reverse_name=f"{field_name}_reverse",
        )

    else:
        return RelationFieldDefinition()


def initialise_field_definitions(model: type[_DeclaredClass]):
    print("=========")
    print("initialising fields on ", model.__name__)

    for field_name, field_info in model.model_fields.items():
        print("---------", field_name)
        """ if is_relatable(field_info.annotation) or is_list_relatable(
            field_info.annotation
        ):
            model._meta.field_definitions.add_field(
                name=field_name,
                field_definition=build_relatable_field_definition(
                    field_name, field_info, model
                ),
            ) """

        if is_list_of_literal(field_info.annotation):
            model._meta.field_definitions.add_field(
                name=field_name,
                field_definition=build_list_field_definition(
                    field_name, field_info, model
                ),
            )

        elif is_literal(field_info.annotation):
            print("is literal")
            print(field_name)
            model._meta.field_definitions.add_field(
                field_name,
                LiteralFieldDefinition(
                    field_on_model=model,
                    field_name=field_name,
                    annotated_type=field_info.annotation,
                    validators=[
                        md for md in field_info.metadata if isinstance(md, BaseMetadata)
                    ],
                ),
            )
