from datetime import date, datetime
from typing import Annotated

from annotated_types import MaxLen

from pangloss.model_setup.field_definitions import (
    ListFieldDefinition,
    LiteralFieldDefinition,
)
from pangloss.model_setup.initialise_field_definitions import is_literal
from pangloss.model_setup.model_bases.document import Document


def test_is_literal():
    assert is_literal(str)
    assert is_literal(int)
    assert is_literal(float)
    assert is_literal(date)
    assert is_literal(datetime)


def test_field_definition_for_literal_field():
    class Statement(Document):
        string: Annotated[str, MaxLen(1)]
        integer: int
        floating: float
        dating: date
        datetiming: datetime

    string_field_def = Statement._meta.fields["string"]
    assert isinstance(string_field_def, LiteralFieldDefinition)

    assert string_field_def.annotated_type is str
    assert string_field_def.field_name == "string"
    assert string_field_def.model_field is Statement.model_fields["string"]
    assert string_field_def.validators == [MaxLen(1)]
    assert string_field_def.field_on_model is Statement


def test_field_definition_for_list_field():
    class Statement(Document):
        items_simple: list[str]
        items_container_validators: Annotated[list[str], MaxLen(2)]
        item_container_and_inner_validators: Annotated[
            list[Annotated[str, MaxLen(10)]],
            MaxLen(2),
        ]

    items_simple_field_def = Statement._meta.fields["items_simple"]
    assert isinstance(items_simple_field_def, ListFieldDefinition)
    assert items_simple_field_def.annotated_type == list[str]
    assert items_simple_field_def.inner_type is str
    assert items_simple_field_def.field_name == "items_simple"
    assert items_simple_field_def.field_on_model is Statement
    assert items_simple_field_def.validators == []

    items_container_validators_def = Statement._meta.fields[
        "items_container_validators"
    ]
    assert isinstance(items_container_validators_def, ListFieldDefinition)
    assert items_container_validators_def.annotated_type == list[str]
    assert items_container_validators_def.inner_type is str
    assert items_container_validators_def.field_name == "items_container_validators"
    assert items_container_validators_def.field_on_model is Statement
    assert items_container_validators_def.validators == [MaxLen(2)]
    assert items_container_validators_def.inner_type_validators == []

    item_container_and_inner_validators_def = Statement._meta.fields[
        "item_container_and_inner_validators"
    ]
    assert isinstance(item_container_and_inner_validators_def, ListFieldDefinition)
    assert (
        item_container_and_inner_validators_def.annotated_type
        == list[Annotated[str, MaxLen(10)]]
    )
    assert (
        item_container_and_inner_validators_def.field_name
        == "item_container_and_inner_validators"
    )
    assert item_container_and_inner_validators_def.field_on_model is Statement
    assert item_container_and_inner_validators_def.validators == [MaxLen(2)]
    assert item_container_and_inner_validators_def.inner_type is str
    assert item_container_and_inner_validators_def.inner_type_validators == [MaxLen(10)]
