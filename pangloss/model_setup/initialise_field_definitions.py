from datetime import date, datetime
from typing import TYPE_CHECKING, Annotated, Any, TypeIs, get_args, get_origin

from annotated_types import BaseMetadata
from pydantic.fields import FieldInfo

from pangloss.model_setup.field_definitions import (
    ListFieldDefinition,
    LiteralFieldDefinition,
)

if TYPE_CHECKING:
    from pangloss.model_setup.model_bases.base_object import _DeclaredClass


LITERAL_TYPES = {str, int, float, date, datetime}


def is_literal(
    annotation: type[Any] | None,
) -> TypeIs[type[str | int | float | date | datetime]]:
    return annotation in LITERAL_TYPES


def build_list_field_definition(
    field_name: str, field_info: FieldInfo, model: type[_DeclaredClass]
) -> ListFieldDefinition:
    assert field_info.annotation
    list_inner_type_tuple = get_args(field_info.annotation)
    assert list_inner_type_tuple
    list_inner_type = list_inner_type_tuple[0]
    inner_type_validators = []
    if get_origin(list_inner_type) is Annotated:
        annotated_inner_type_tuple = get_args(list_inner_type)
        assert annotated_inner_type_tuple
        list_inner_type = annotated_inner_type_tuple[0]
        inner_type_validators = [
            arg for arg in annotated_inner_type_tuple if isinstance(arg, BaseMetadata)
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


def initialise_field_definitions(model: type[_DeclaredClass]):

    for field_name, field_info in model.model_fields.items():
        if get_origin(field_info.annotation) is list:
            model._meta.field_definitions.add_field(
                name=field_name,
                field_definition=build_list_field_definition(
                    field_name, field_info, model
                ),
            )

        elif is_literal(field_info.annotation):
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
