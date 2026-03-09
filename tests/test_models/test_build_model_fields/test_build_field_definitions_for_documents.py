from datetime import date, datetime
from typing import Annotated

from annotated_types import MaxLen

from pangloss.model_setup.field_definitions import (
    ListFieldDefinition,
    LiteralFieldDefinition,
)
from pangloss.model_setup.initialise_field_definitions import (
    is_list_of_literal,
    is_list_relatable,
    is_literal,
    is_relatable,
)
from pangloss.model_setup.model_bases.configs import EntityFieldConfig, RelationConfig
from pangloss.model_setup.model_bases.document import Document
from pangloss.model_setup.model_bases.edge_model import EdgeModel
from pangloss.model_setup.model_bases.entity import Entity
from pangloss.model_setup.model_bases.helpers import ViaEdge


def test_is_literal():
    class Statement(Document):
        pass

    assert is_literal(str)
    assert is_literal(int)
    assert is_literal(float)
    assert is_literal(date)
    assert is_literal(datetime)

    assert not is_literal(Statement)
    assert not is_literal(None)


def test_is_list_of_literal():
    class Statement(Document):
        pass

    assert not is_list_of_literal(str)

    assert is_list_of_literal(list[str])

    assert not is_list_of_literal(list[Statement])

    assert is_list_of_literal(list[Annotated[str, MaxLen(1)]])

    assert not is_list_of_literal(list[str | int])


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


def test_is_relatable():
    class ToDogEdge(EdgeModel):
        when: date

    class Factoid(Document):
        pass

    class Statement(Document):
        concerns_dog: Dog
        concerns_dog_list: list[Dog]
        concerns_dog_annotated: Annotated[
            list[ViaEdge[Dog, ToDogEdge]],
            EntityFieldConfig(reverse_name="is_concerned_in"),
        ]
        concerns_animal_multiple: Annotated[
            list[ViaEdge[Dog, ToDogEdge]] | Cat,
            RelationConfig(reverse_name="is_animal_in"),
        ]

    class Dog(Entity):
        name: str

    class Cat(Entity):
        name: str

    assert is_relatable(Statement)
    assert is_relatable(Dog)
    assert is_relatable(Factoid)
    assert is_relatable(ViaEdge[Dog, ToDogEdge])
    assert is_relatable(Dog | Cat)
    assert is_list_relatable(list[ViaEdge[Dog, ToDogEdge]])
    assert is_list_relatable(list[Dog])
    assert is_list_relatable(list[Statement])
    assert is_list_relatable(list[Factoid])


def test_build_relation_field_definitions():
    class ToDogEdge(EdgeModel):
        when: date

    class Factoid(Document):
        has_statements: Statement

    class Dog(Entity):
        name: str

    class Cat(Entity):
        name: str

    class Statement(Document):
        concerns_dog: Dog
        concerns_dog_list: list[Dog]
        concerns_dog_annotated: Annotated[
            list[ViaEdge[Dog, ToDogEdge]],
            EntityFieldConfig(reverse_name="is_concerned_in"),
        ]
        concerns_animal_multiple: Annotated[
            list[ViaEdge[Dog, ToDogEdge]] | Cat,
            RelationConfig(reverse_name="is_animal_in"),
        ]

    assert Statement._meta.fields["concerns_dog"]
