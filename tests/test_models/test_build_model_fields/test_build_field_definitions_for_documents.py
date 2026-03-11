from datetime import date, datetime
from types import UnionType
from typing import Annotated, get_args, get_origin

from annotated_types import MaxLen

from pangloss.model_setup.field_definitions import (
    ListFieldDefinition,
    LiteralFieldDefinition,
    RelationFieldDefinition,
    RelationToEntity,
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


def test_meta_fields():

    class Dog(Entity):
        name: str

    class Cat(Entity):
        name: str

    class Tabby(Cat):
        name: str

    class SubTabby(Tabby):
        name: str

    class Statement(Document):
        label: str

    class Action(Statement):
        label: str

    assert Dog._meta is not Cat._meta

    assert Cat._meta is not Tabby._meta
    assert Cat._meta.field_definitions is not Tabby._meta.field_definitions
    assert Cat._meta.fields is not Tabby._meta.fields

    assert Cat._meta is not Dog._meta
    assert Tabby._meta is not Cat._meta

    assert Cat._meta._owner_class is Cat
    assert Dog._meta._owner_class is Dog
    assert Tabby._meta._owner_class is Tabby

    assert Dog._meta.fields["name"]
    assert Cat._meta.fields["name"]
    assert Tabby._meta.fields["name"]

    assert Dog._meta.fields["name"].field_on_model is Dog
    assert Cat._meta.fields["name"].field_on_model is Cat
    assert Tabby._meta.fields["name"].field_on_model is Tabby

    assert Statement._meta.fields
    assert Action._meta is not Statement._meta
    assert Action._meta.field_definitions is not Statement._meta.field_definitions

    assert Statement._meta.fields["label"]
    assert Action._meta.fields["label"]

    assert Statement._meta.fields["label"].field_on_model is Statement
    assert Action._meta.fields["label"].field_on_model is Action


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


def test_build_relation_field_definition_with_simple():

    class Dog(Entity):
        name: str

    class Puppy(Dog):
        pass

    class Statement(Document):
        concerns_dog: Dog

    assert Dog._meta.field_definitions

    dog_name_field = Dog._meta.fields["name"]
    assert dog_name_field
    assert isinstance(dog_name_field, LiteralFieldDefinition)
    assert dog_name_field.annotated_type is str
    assert dog_name_field.field_on_model is Dog
    assert dog_name_field.field_name == "name"
    assert dog_name_field.validators == []

    statement_concerns_dog_field = Statement._meta.fields["concerns_dog"]
    assert statement_concerns_dog_field
    assert isinstance(statement_concerns_dog_field, RelationFieldDefinition)
    assert statement_concerns_dog_field.annotated_type is Dog
    assert statement_concerns_dog_field.field_on_model is Statement
    assert statement_concerns_dog_field.field_name == "concerns_dog"
    assert statement_concerns_dog_field.type_options == set(
        [
            RelationToEntity(annotated_type=Dog),
            RelationToEntity(annotated_type=Puppy),
        ]
    )
    assert statement_concerns_dog_field.wrapper is None


def test_build_relation_field_definition_with_simple_out_of_order_declaration():
    """Puppy is defined *after* Statement but should still be considered a subclass
    of Dog, which was the only known thing at the point where Statement was
    declared"""

    class Dog(Entity):
        name: str

    class Statement(Document):
        concerns_dog: Dog

    class Puppy(Dog):
        pass

    assert Dog._meta.field_definitions

    dog_name_field = Dog._meta.fields["name"]
    assert dog_name_field
    assert isinstance(dog_name_field, LiteralFieldDefinition)
    assert dog_name_field.annotated_type is str
    assert dog_name_field.field_on_model is Dog
    assert dog_name_field.field_name == "name"
    assert dog_name_field.validators == []

    statement_concerns_dog_field = Statement._meta.fields["concerns_dog"]
    assert statement_concerns_dog_field
    assert isinstance(statement_concerns_dog_field, RelationFieldDefinition)
    assert statement_concerns_dog_field.annotated_type is Dog
    assert statement_concerns_dog_field.field_on_model is Statement
    assert statement_concerns_dog_field.field_name == "concerns_dog"
    assert statement_concerns_dog_field.type_options == set(
        [
            RelationToEntity(annotated_type=Dog),
            RelationToEntity(annotated_type=Puppy),
        ]
    )
    assert statement_concerns_dog_field.wrapper is None


def test_build_relation_field_definition_with_simple_list():
    class Dog(Entity):
        name: str

    class Puppy(Dog):
        pass

    class Statement(Document):
        concerns_dog_list: list[Dog]
        # concerns_dog_cat: Dog | Cat
        # concerns_dog_cat_list: list[Dog | Cat]
        # concerns_dog_annotated: Annotated[
        #    list[ViaEdge[Dog, ToDogEdge]],
        #    RelationConfig(reverse_name="is_concerned_in"),
        # ]
        # concerns_animal_multiple: Annotated[
        #    list[ViaEdge[Dog, ToDogEdge] | Cat],
        #    RelationConfig(reverse_name="is_animal_in"),
        # ]

    statement_concerns_dog_list_field = Statement._meta.fields["concerns_dog_list"]
    assert statement_concerns_dog_list_field
    assert isinstance(statement_concerns_dog_list_field, RelationFieldDefinition)
    assert get_origin(statement_concerns_dog_list_field.annotated_type) is list
    assert get_args(statement_concerns_dog_list_field.annotated_type)[0] is Dog
    assert statement_concerns_dog_list_field.field_on_model is Statement
    assert statement_concerns_dog_list_field.field_name == "concerns_dog_list"
    assert statement_concerns_dog_list_field.type_options == set(
        [
            RelationToEntity(annotated_type=Dog),
            RelationToEntity(annotated_type=Puppy),
        ]
    )
    assert statement_concerns_dog_list_field.wrapper is list


def test_build_relation_field_definition_with_simple_union():
    class Dog(Entity):
        name: str

    class Puppy(Dog):
        pass

    class Cat(Entity):
        pass

    class Statement(Document):
        concerns_dog_cat: Dog | Cat

    statement_concerns_dog_cat_field = Statement._meta.fields["concerns_dog_cat"]
    assert statement_concerns_dog_cat_field
    assert isinstance(statement_concerns_dog_cat_field, RelationFieldDefinition)
    assert get_origin(statement_concerns_dog_cat_field.annotated_type) is UnionType
    assert get_args(statement_concerns_dog_cat_field.annotated_type) == (Dog, Cat)
    assert statement_concerns_dog_cat_field.field_on_model is Statement
    assert statement_concerns_dog_cat_field.field_name == "concerns_dog_cat"
    assert statement_concerns_dog_cat_field.reverse_name == "concerns_dog_cat_reverse"
    assert statement_concerns_dog_cat_field.type_options == set(
        [
            RelationToEntity(annotated_type=Dog),
            RelationToEntity(annotated_type=Puppy),
            RelationToEntity(annotated_type=Cat),
        ]
    )
    assert statement_concerns_dog_cat_field.wrapper is None


def test_build_relation_field_definition_with_list_union():

    class Statement(Document):
        concerns_dog_cat_list: list[Dog | Cat]

    class Dog(Entity):
        name: str

    class Puppy(Dog):
        pass

    class Cat(Entity):
        pass

    statement_concerns_dog_cat_field = Statement._meta.fields["concerns_dog_cat_list"]
    assert statement_concerns_dog_cat_field
    assert isinstance(statement_concerns_dog_cat_field, RelationFieldDefinition)
    assert get_origin(statement_concerns_dog_cat_field.annotated_type) is list
    assert (
        get_origin(get_args(statement_concerns_dog_cat_field.annotated_type)[0])
        is UnionType
    )
    assert get_args(get_args(statement_concerns_dog_cat_field.annotated_type)[0]) == (
        Dog,
        Cat,
    )
    assert statement_concerns_dog_cat_field.field_name == "concerns_dog_cat_list"
    assert statement_concerns_dog_cat_field.field_on_model is Statement
