from datetime import date, datetime
from types import UnionType
from typing import Annotated, TypeVar, get_args, get_origin

import pytest
from annotated_types import MaxLen

from pangloss.exceptions import PanglossModelError
from pangloss.model_setup.field_definitions import (
    EmbeddedFieldDefinition,
    EmbeddedOption,
    FieldFulfilment,
    FieldSubclassing,
    ListFieldDefinition,
    LiteralFieldDefinition,
    ParameterTypeOptions,
    RelationFieldDefinition,
    RelationToConjunction,
    RelationToDocument,
    RelationToEntity,
    RelationToReifiedRelation,
    RelationToSemanticSpace,
    RelationToTypeVar,
)
from pangloss.model_setup.initialise_field_definitions import (
    get_fields_on_model,
    is_embedded,
    is_list_of_literal,
    is_list_relatable,
    is_literal,
    is_relatable,
    is_single_relatable,
    is_union_of_embedded,
)
from pangloss.model_setup.model_bases.configs import RelationConfig
from pangloss.model_setup.model_bases.conjunction import Conjunction
from pangloss.model_setup.model_bases.document import Document
from pangloss.model_setup.model_bases.edge_model import EdgeModel
from pangloss.model_setup.model_bases.embedded import Embedded, EmbeddedMeta
from pangloss.model_setup.model_bases.entity import Entity, EntityMeta
from pangloss.model_setup.model_bases.helpers import Fulfils, ViaEdge
from pangloss.model_setup.model_bases.reified_relation import ReifiedRelation
from pangloss.model_setup.model_bases.semantic_space import SemanticSpace
from pangloss.model_setup.model_bases.trait import NonHeritableTrait, Trait
from pangloss.model_setup.utils import get_all_parent_classes


def test_meta_fields():
    """Ensure each model has distinct _meta and field definitions."""

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
    """Verify that primitives and builtin types are treated as literals."""

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
    """Verify that only list[...] of literals are treated as literal lists."""

    class Statement(Document):
        pass

    assert not is_list_of_literal(str)

    assert is_list_of_literal(list[str])

    assert not is_list_of_literal(list[Statement])

    assert is_list_of_literal(list[Annotated[str, MaxLen(1)]])

    assert not is_list_of_literal(list[str | int])


def test_field_definition_for_literal_field():
    """Build field definitions for literal-typed fields on a Document."""

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
    """Build field definitions for list-typed fields and validate nested validators."""

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
    """Validate that various types are recognized as relatables for relation fields."""

    class ToDogEdge(EdgeModel):
        when: date

    class Factoid(Document):
        pass

    class Statement(Document):
        concerns_dog: Dog
        concerns_dog_list: list[Dog]
        concerns_dog_annotated: Annotated[
            list[ViaEdge[Dog, ToDogEdge]],
            RelationConfig(reverse_name="is_concerned_in"),
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


def test_is_relatable_on_semantic_space():
    class Negative[Content](SemanticSpace[Content]):
        pass

    class Statement(Document):
        pass

    assert is_relatable(Negative[Statement])


def test_is_relatable_on_conjunction():
    class Action(Document):
        pass

    class Alternative[T](Conjunction):
        alternatives: T

    assert is_relatable(Alternative)
    assert is_relatable(Alternative[Action])


def test_is_embedded():
    class Thing(Embedded):
        pass

    assert is_embedded(Thing)


def test_is_union_embedded():
    class Thing(Embedded):
        pass

    class Thong(Embedded):
        pass

    assert is_union_of_embedded(Thing | Thong)


def test_build_relation_field_definition_with_simple():
    """Build a relation field to a single Entity and validate inferred options."""

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
    """Ensure subclasses declared after a relation field are still discovered."""

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
    """Build a relation field for a list of Entities and confirm wrapper is list."""

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
    """Confirm union-typed relation fields produce multiple relation type options."""

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
    """Verify list-of-union relation fields correctly preserve union typing."""

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
    assert statement_concerns_dog_cat_field.type_options == set(
        [
            RelationToEntity(annotated_type=Dog),
            RelationToEntity(annotated_type=Puppy),
            RelationToEntity(annotated_type=Cat),
        ]
    )


def test_build_relation_field_with_self_reference():
    """Ensure self-referential relation fields include both self and other types."""

    class Act(Document):
        pass

    class Order(Document):
        thing_ordered: Act | Order

    order_thing_ordered_field = Order._meta.fields["thing_ordered"]
    assert order_thing_ordered_field
    assert order_thing_ordered_field.annotated_type == Act | Order
    assert isinstance(order_thing_ordered_field, RelationFieldDefinition)
    assert order_thing_ordered_field.type_options == set(
        [
            RelationToDocument(annotated_type=Act),
            RelationToDocument(annotated_type=Order),
        ]
    )


def test_build_relation_field_definition_with_annotation():
    class Dog(Entity):
        pass

    class Puppy(Entity):
        pass

    class Statement(Document):
        concerns_dog_annotated: Annotated[
            Dog,
            RelationConfig(reverse_name="is_concerned_in"),
        ]

    statement_concerns_dog_annotated_field = Statement._meta.fields[
        "concerns_dog_annotated"
    ]
    assert statement_concerns_dog_annotated_field
    assert isinstance(statement_concerns_dog_annotated_field, RelationFieldDefinition)
    assert statement_concerns_dog_annotated_field.field_name == "concerns_dog_annotated"
    assert statement_concerns_dog_annotated_field.field_on_model is Statement
    assert statement_concerns_dog_annotated_field.reverse_name == "is_concerned_in"
    assert statement_concerns_dog_annotated_field.annotated_type is Dog
    assert statement_concerns_dog_annotated_field.type_options == set(
        [RelationToEntity(annotated_type=Dog)]
    )
    assert statement_concerns_dog_annotated_field.wrapper is None


def test_build_relation_field_definition_with_annotation_list():
    """Ensure annotated list relations preserve wrapper and reverse name."""

    class Dog(Entity):
        pass

    class Puppy(Entity):
        pass

    class Statement(Document):
        concerns_dog_annotated: Annotated[
            list[Dog],
            RelationConfig(reverse_name="is_concerned_in"),
        ]

    statement_concerns_dog_annotated_field = Statement._meta.fields[
        "concerns_dog_annotated"
    ]
    assert statement_concerns_dog_annotated_field
    assert isinstance(statement_concerns_dog_annotated_field, RelationFieldDefinition)
    assert statement_concerns_dog_annotated_field.field_name == "concerns_dog_annotated"
    assert statement_concerns_dog_annotated_field.field_on_model is Statement
    assert statement_concerns_dog_annotated_field.reverse_name == "is_concerned_in"
    assert get_origin(statement_concerns_dog_annotated_field.annotated_type) is list
    assert get_args(statement_concerns_dog_annotated_field.annotated_type)[0] is Dog
    assert statement_concerns_dog_annotated_field.type_options == set(
        [RelationToEntity(annotated_type=Dog)]
    )


def test_build_relation_field_with_relation_to_document():
    class Statement(Document):
        action_carried_out: Annotated[
            Action,
            RelationConfig(reverse_name="was carried out in"),
        ]

    class Action(Document):
        pass

    statement_action_carried_out_field = Statement._meta.fields["action_carried_out"]
    assert statement_action_carried_out_field
    assert isinstance(statement_action_carried_out_field, RelationFieldDefinition)
    assert statement_action_carried_out_field.field_name == "action_carried_out"
    assert statement_action_carried_out_field.reverse_name == "was_carried_out_in"
    assert statement_action_carried_out_field.type_options == set(
        [RelationToDocument(annotated_type=Action)]
    )


def test_edge_model_does_not_have_invalid_fields():
    """Ensure EdgeModel fields reject non-literal types like Entity references."""

    class Dog(Entity):
        pass

    with pytest.raises(PanglossModelError):

        class EdgeToDog(EdgeModel):
            dog: Dog


def test_build_field_for_edge_model():

    class EdgeToDog(EdgeModel):
        when: str
        strategies: list[int]

    edge_to_dog_when_field = EdgeToDog._meta.fields["when"]
    assert isinstance(edge_to_dog_when_field, LiteralFieldDefinition)
    assert edge_to_dog_when_field.field_on_model is EdgeToDog
    assert edge_to_dog_when_field.annotated_type is str
    assert edge_to_dog_when_field.field_name == "when"


def test_relation_via_edge_model():
    """Verify via-edge relations are represented with edge model metadata."""

    class Dog(Entity):
        pass

    class EdgeToDog(EdgeModel):
        when: str

    class Statement(Document):
        concerns_dog: ViaEdge[Dog, EdgeToDog]

    statement_concerns_dog_field = Statement._meta.fields["concerns_dog"]
    assert statement_concerns_dog_field
    assert isinstance(statement_concerns_dog_field, RelationFieldDefinition)
    assert statement_concerns_dog_field.type_options == set(
        [RelationToEntity(annotated_type=Dog, edge_model=EdgeToDog)]
    )


def test_relation_via_edge_model_to_union():
    """Ensure via-edge relations in unions retain all possible entity/edge combos."""

    class Animal(Entity):
        _meta = EntityMeta(abstract=True)

    class Dog(Animal):
        pass

    class Puppy(Dog):
        pass

    class Cat(Animal):
        pass

    class Biscuit(Entity):
        pass

    class EdgeToAnimal(EdgeModel):
        when: str

    class Statement(Document):
        concerns_thing: Annotated[
            list[Biscuit | ViaEdge[Animal, EdgeToAnimal]],
            RelationConfig(reverse_name="is concerned in"),
        ]

    statement_concerns_thing_field = Statement._meta.fields["concerns_thing"]
    assert statement_concerns_thing_field
    assert isinstance(statement_concerns_thing_field, RelationFieldDefinition)
    assert statement_concerns_thing_field.field_name == "concerns_thing"
    assert statement_concerns_thing_field.field_on_model is Statement
    assert (
        statement_concerns_thing_field.annotated_type
        == list[Biscuit | ViaEdge[Animal, EdgeToAnimal]]
    )
    assert statement_concerns_thing_field.type_options == set(
        [
            RelationToEntity(annotated_type=Biscuit),
            RelationToEntity(annotated_type=Dog, edge_model=EdgeToAnimal),
            RelationToEntity(annotated_type=Puppy, edge_model=EdgeToAnimal),
            RelationToEntity(annotated_type=Cat, edge_model=EdgeToAnimal),
        ]
    )


def test_build_meta_fields_for_reified_relation():
    """Verify ReifiedRelation fields correctly use RelationToTypeVar for type vars."""

    class Identification[Target](ReifiedRelation[Target]):
        target: list[Target]

    assert Identification._meta
    identification_target_field = Identification._meta.fields["target"]
    assert isinstance(identification_target_field, RelationFieldDefinition)
    assert identification_target_field.field_name == "target"
    assert identification_target_field.field_on_model is Identification
    assert get_origin(identification_target_field.annotated_type) is list
    typevar_arg = get_args(identification_target_field.annotated_type)[0]
    assert isinstance(typevar_arg, TypeVar)
    assert typevar_arg.__name__ == "Target"

    target_param = Identification.__pydantic_generic_metadata__["parameters"][0]
    assert identification_target_field.type_options == set(
        [RelationToTypeVar(annotated_type=target_param, type_var_name="Target")]
    )


def test_relation_via_reified():
    """Ensure relations via ReifiedRelation work, even with out-of-order declarations."""

    class Statement(Document):
        concerns_dog: Identification[Dog]

    class Dog(Entity):
        pass

    class Puppy(Dog):
        pass

    class Identification[Target](ReifiedRelation[Target]):
        target: list[Target]

    assert is_single_relatable(Identification[Dog])

    statement_concerns_dog_field = Statement._meta.fields["concerns_dog"]
    assert statement_concerns_dog_field
    assert isinstance(statement_concerns_dog_field, RelationFieldDefinition)
    assert statement_concerns_dog_field.field_name == "concerns_dog"
    assert statement_concerns_dog_field.field_on_model is Statement
    assert statement_concerns_dog_field.annotated_type == Identification[Dog]
    statement_concerns_dog_field_type_option = (
        statement_concerns_dog_field.type_options.pop()
    )
    assert isinstance(
        statement_concerns_dog_field_type_option, RelationToReifiedRelation
    )
    assert (
        statement_concerns_dog_field_type_option.annotated_type == Identification[Dog]
    )
    assert (
        statement_concerns_dog_field_type_option.reified_relation_type is Identification
    )
    statement_concerns_dog_field_type_option_paramter_type_options_target = (
        statement_concerns_dog_field_type_option.parameter_type_options["Target"]
    )
    assert statement_concerns_dog_field_type_option_paramter_type_options_target
    assert isinstance(
        statement_concerns_dog_field_type_option_paramter_type_options_target,
        ParameterTypeOptions,
    )
    assert (
        statement_concerns_dog_field_type_option_paramter_type_options_target.type_var
        is Identification.__pydantic_generic_metadata__["parameters"][0]
    )
    assert (
        statement_concerns_dog_field_type_option_paramter_type_options_target.type_var_name
        == "Target"
    )
    assert (
        statement_concerns_dog_field_type_option_paramter_type_options_target.type_options
        == frozenset(
            [
                RelationToEntity(annotated_type=Dog),
                RelationToEntity(annotated_type=Puppy),
            ]
        )
    )


def test_relation_via_reified_with_two_params():
    class Statement(Document):
        concerns_dog: WithProxy[Dog, Cat]

    class Dog(Entity):
        pass

    class WithProxy[Target, Proxy](ReifiedRelation[Target]):
        target: list[Target]
        proxy: list[Proxy]

    class Puppy(Dog):
        pass

    class Cat(Entity):
        pass

    assert is_single_relatable(WithProxy[Dog, Cat])

    statement_concerns_dog_field = Statement._meta.fields["concerns_dog"]
    assert statement_concerns_dog_field
    assert isinstance(statement_concerns_dog_field, RelationFieldDefinition)
    assert statement_concerns_dog_field.field_name == "concerns_dog"
    assert statement_concerns_dog_field.field_on_model is Statement
    assert statement_concerns_dog_field.annotated_type == WithProxy[Dog, Cat]
    statement_concerns_dog_field_type_option = (
        statement_concerns_dog_field.type_options.pop()
    )
    assert isinstance(
        statement_concerns_dog_field_type_option, RelationToReifiedRelation
    )
    assert (
        statement_concerns_dog_field_type_option.annotated_type == WithProxy[Dog, Cat]
    )
    assert statement_concerns_dog_field_type_option.reified_relation_type is WithProxy
    statement_concerns_dog_field_type_option_paramter_type_options_target = (
        statement_concerns_dog_field_type_option.parameter_type_options["Target"]
    )
    assert statement_concerns_dog_field_type_option_paramter_type_options_target
    assert isinstance(
        statement_concerns_dog_field_type_option_paramter_type_options_target,
        ParameterTypeOptions,
    )
    assert (
        statement_concerns_dog_field_type_option_paramter_type_options_target.type_var
        is WithProxy.__pydantic_generic_metadata__["parameters"][0]
    )
    assert (
        statement_concerns_dog_field_type_option_paramter_type_options_target.type_var_name
        == "Target"
    )
    assert (
        statement_concerns_dog_field_type_option_paramter_type_options_target.type_options
        == frozenset(
            [
                RelationToEntity(annotated_type=Dog),
                RelationToEntity(annotated_type=Puppy),
            ]
        )
    )

    statement_concerns_dog_field_type_option_paramter_type_options_proxy = (
        statement_concerns_dog_field_type_option.parameter_type_options["Proxy"]
    )
    assert statement_concerns_dog_field_type_option_paramter_type_options_proxy
    assert isinstance(
        statement_concerns_dog_field_type_option_paramter_type_options_proxy,
        ParameterTypeOptions,
    )
    assert (
        statement_concerns_dog_field_type_option_paramter_type_options_proxy.type_var
        is WithProxy.__pydantic_generic_metadata__["parameters"][1]
    )
    assert (
        statement_concerns_dog_field_type_option_paramter_type_options_proxy.type_var_name
        == "Proxy"
    )
    assert (
        statement_concerns_dog_field_type_option_paramter_type_options_proxy.type_options
        == frozenset(
            [
                RelationToEntity(annotated_type=Cat),
            ]
        )
    )


def test_relation_via_double_reified():
    class Dog(Entity):
        pass

    class WithProxy[Target, Proxy](ReifiedRelation[Target]):
        target: list[Target]
        proxy: list[Proxy]

    class Statement(Document):
        concerns_dog: WithProxy[Identification[Dog], Identification[Cat]]

    class Puppy(Dog):
        pass

    class Cat(Entity):
        pass

    class Identification[Target](ReifiedRelation[Target]):
        target: list[Target]

    statement_concerns_dog_field = Statement._meta.fields["concerns_dog"]
    assert statement_concerns_dog_field
    assert isinstance(statement_concerns_dog_field, RelationFieldDefinition)
    assert statement_concerns_dog_field.field_name == "concerns_dog"
    assert statement_concerns_dog_field.field_on_model is Statement
    assert (
        statement_concerns_dog_field.annotated_type
        == WithProxy[Identification[Dog], Identification[Cat]]
    )

    statement_concerns_dog_field_type_option = (
        statement_concerns_dog_field.type_options.pop()
    )
    assert isinstance(
        statement_concerns_dog_field_type_option, RelationToReifiedRelation
    )
    assert (
        statement_concerns_dog_field_type_option.annotated_type
        == WithProxy[Identification[Dog], Identification[Cat]]
    )
    assert statement_concerns_dog_field_type_option.reified_relation_type is WithProxy

    target_param_opts = statement_concerns_dog_field_type_option.parameter_type_options[
        "Target"
    ]
    assert isinstance(target_param_opts, ParameterTypeOptions)
    assert target_param_opts.type_var_name == "Target"

    target_type_option = next(iter(target_param_opts.type_options))
    assert isinstance(target_type_option, RelationToReifiedRelation)
    assert target_type_option.annotated_type == Identification[Dog]

    inner_target_param = target_type_option.parameter_type_options["Target"]
    assert isinstance(inner_target_param, ParameterTypeOptions)
    assert inner_target_param.type_options == frozenset(
        [
            RelationToEntity(annotated_type=Dog),
            RelationToEntity(annotated_type=Puppy),
        ]
    )

    proxy_param_opts = statement_concerns_dog_field_type_option.parameter_type_options[
        "Proxy"
    ]
    assert isinstance(proxy_param_opts, ParameterTypeOptions)
    assert proxy_param_opts.type_var_name == "Proxy"

    proxy_type_option = next(iter(proxy_param_opts.type_options))
    assert isinstance(proxy_type_option, RelationToReifiedRelation)
    assert proxy_type_option.annotated_type == Identification[Cat]

    inner_proxy_param = proxy_type_option.parameter_type_options["Target"]
    assert inner_proxy_param.type_options == frozenset(
        [RelationToEntity(annotated_type=Cat)]
    )


def test_embedded_node():
    class Date(Embedded):
        _meta = EmbeddedMeta(abstract=True)
        when: datetime

    class Statement(Document):
        date: Date

    class SpecialDate(Date):
        pass

    statement_date_field = Statement._meta.fields["date"]
    assert statement_date_field
    assert isinstance(statement_date_field, EmbeddedFieldDefinition)
    assert statement_date_field.annotated_type is Date
    assert statement_date_field.field_name == "date"
    assert statement_date_field.field_on_model is Statement
    assert statement_date_field.type_options == set(
        [
            EmbeddedOption(annotated_type=SpecialDate),
        ]
    )


def test_semantic_space_fields():
    class Negative[Contents](SemanticSpace[Contents]):
        pass

    class ReallyNegative[Contents](Negative[Contents]):
        stuff: int

    class NonParameterisedNegative(Negative):
        pass

    negative_contents_field = Negative._meta.fields["contents"]
    assert negative_contents_field
    assert isinstance(negative_contents_field, RelationFieldDefinition)
    assert isinstance(negative_contents_field.annotated_type, TypeVar)
    assert negative_contents_field.annotated_type.__name__ == "Contents"
    assert negative_contents_field.field_name == "contents"
    assert negative_contents_field.field_on_model is Negative

    really_negative_contents_field = ReallyNegative._meta.fields["contents"]
    assert really_negative_contents_field
    assert isinstance(really_negative_contents_field, RelationFieldDefinition)
    assert isinstance(really_negative_contents_field.annotated_type, TypeVar)
    assert really_negative_contents_field.annotated_type.__name__ == "Contents"
    assert really_negative_contents_field.field_name == "contents"
    assert really_negative_contents_field.field_on_model is ReallyNegative
    really_negative_stuff_field = ReallyNegative._meta.fields["stuff"]
    assert isinstance(really_negative_stuff_field, LiteralFieldDefinition)

    # Check still works with a SemanticSpace without declared parameters
    non_parameterised_negative_contents_field = NonParameterisedNegative._meta.fields[
        "contents"
    ]
    assert non_parameterised_negative_contents_field
    assert isinstance(
        non_parameterised_negative_contents_field, RelationFieldDefinition
    )
    assert isinstance(non_parameterised_negative_contents_field.annotated_type, TypeVar)
    assert (
        non_parameterised_negative_contents_field.annotated_type.__name__ == "Contents"
    )
    assert non_parameterised_negative_contents_field.field_name == "contents"
    assert (
        non_parameterised_negative_contents_field.field_on_model
        is NonParameterisedNegative
    )


def test_relation_to_semantic_space():
    class Negative[Contents](SemanticSpace[Contents]):
        pass

    class Statement(Document):
        action: Negative[Task]

    class Task(Document):
        pass

    statement_action_field = Statement._meta.fields["action"]
    assert statement_action_field
    assert isinstance(statement_action_field, RelationFieldDefinition)
    assert statement_action_field.field_name == "action"
    assert statement_action_field.field_on_model is Statement
    assert statement_action_field.annotated_type == Negative[Task]
    assert len(statement_action_field.type_options) == 1

    content_type_option = statement_action_field.type_options.pop()
    assert isinstance(content_type_option, RelationToSemanticSpace)
    assert content_type_option.annotated_type == Negative[Task]
    assert content_type_option.edge_model is None
    assert content_type_option.semantic_space_type is Negative

    content_param_type_option = content_type_option.parameter_type_options["Contents"]
    assert content_param_type_option
    assert isinstance(content_param_type_option.type_var, TypeVar)
    assert content_param_type_option.type_var.__name__ == "Contents"
    assert content_param_type_option.type_var_name == "Contents"
    assert len(content_param_type_option.type_options) == 1
    assert content_param_type_option.type_options == frozenset(
        [RelationToDocument(annotated_type=Task)]
    )


def test_relation_to_semantic_space_includes_subclass():
    class Negative[Contents](SemanticSpace[Contents]):
        pass

    class Statement(Document):
        action: Negative[Task]

    class Task(Document):
        pass

    class ReallyNegative(Negative):
        pass

    statement_action_field = Statement._meta.fields["action"]
    assert statement_action_field
    assert isinstance(statement_action_field, RelationFieldDefinition)
    assert statement_action_field.field_name == "action"
    assert statement_action_field.field_on_model is Statement
    assert statement_action_field.annotated_type == Negative[Task]

    assert len(statement_action_field.type_options) == 2

    statement_action_field_type_options = statement_action_field.type_options

    type_option_0 = [
        t
        for t in statement_action_field_type_options
        if isinstance(t, RelationToSemanticSpace) and t.semantic_space_type is Negative
    ][0]
    assert isinstance(type_option_0, RelationToSemanticSpace)
    assert type_option_0.annotated_type == Negative[Task]
    assert type_option_0.edge_model is None
    assert type_option_0.semantic_space_type is Negative
    type_options_0_contents = type_option_0.parameter_type_options["Contents"]
    assert type_options_0_contents.type_var_name == "Contents"
    assert type_options_0_contents.type_options == frozenset(
        [RelationToDocument(annotated_type=Task)]
    )

    type_option_1 = [
        t
        for t in statement_action_field_type_options
        if isinstance(t, RelationToSemanticSpace)
        and t.semantic_space_type is ReallyNegative
    ][0]
    assert type_option_1.annotated_type is Negative[Task]
    assert type_option_1.edge_model is None
    assert type_option_1.semantic_space_type is ReallyNegative
    type_options_1_contents = type_option_1.parameter_type_options["Contents"]
    assert type_options_1_contents.type_var_name == "Contents"
    assert type_options_1_contents.type_options == frozenset(
        [RelationToDocument(annotated_type=Task)]
    )


def test_union_of_semantic_space_with_regular_type():
    class Negative[Content](SemanticSpace[Content]):
        pass

    class ReallyNegative(Negative):
        pass

    class Statement(Document):
        action: Task | Negative[Task]

    class Task(Document):
        pass

    statement_action_field = Statement._meta.fields["action"]
    assert statement_action_field
    assert isinstance(statement_action_field, RelationFieldDefinition)
    assert statement_action_field.field_name == "action"
    assert statement_action_field.field_on_model is Statement
    assert len(statement_action_field.type_options) == 3

    assert any(
        isinstance(option, RelationToDocument) and option.annotated_type is Task
        for option in statement_action_field.type_options
    )

    negative_option = next(
        option
        for option in statement_action_field.type_options
        if isinstance(option, RelationToSemanticSpace)
        and option.semantic_space_type is Negative
    )
    assert negative_option.annotated_type == Negative[Task]
    negative_contents_param = negative_option.parameter_type_options["Content"]
    assert negative_contents_param.type_var.__name__ == "Content"
    assert negative_contents_param.type_options == frozenset(
        [RelationToDocument(annotated_type=Task)]
    )

    really_negative_option = next(
        option
        for option in statement_action_field.type_options
        if isinstance(option, RelationToSemanticSpace)
        and option.semantic_space_type is ReallyNegative
    )
    assert really_negative_option.annotated_type == Negative[Task]
    really_negative_contents_param = really_negative_option.parameter_type_options[
        "Content"
    ]
    assert really_negative_contents_param.type_var.__name__ == "Content"
    assert really_negative_contents_param.type_options == frozenset(
        [RelationToDocument(annotated_type=Task)]
    )


def test_conjunction_fields():
    class Alternative[T](Conjunction):
        alternatives: T

    assert Alternative._meta.fields
    alternative_alternatives_field = Alternative._meta.fields["alternatives"]
    assert isinstance(alternative_alternatives_field, RelationFieldDefinition)
    assert alternative_alternatives_field.field_name == "alternatives"
    assert alternative_alternatives_field.field_on_model is Alternative
    assert isinstance(alternative_alternatives_field.annotated_type, TypeVar)
    assert alternative_alternatives_field.annotated_type.__name__ == "T"
    assert alternative_alternatives_field.type_options
    type_option = alternative_alternatives_field.type_options.pop()
    assert isinstance(type_option, RelationToTypeVar)
    assert isinstance(type_option.annotated_type, TypeVar)
    assert type_option.annotated_type.__name__ == "T"
    assert type_option.edge_model is None
    assert type_option.type_var_name == "T"


def test_conjunction_fields_with_two_list_fields():
    class Causes[Cause, Result](Conjunction):
        cause: list[Cause]
        result: list[Result]

    assert Causes._meta.fields

    cause_field = Causes._meta.fields["cause"]
    assert isinstance(cause_field, RelationFieldDefinition)
    assert cause_field.field_name == "cause"
    assert cause_field.field_on_model is Causes
    assert get_origin(cause_field.annotated_type) is list
    cause_inner = get_args(cause_field.annotated_type)[0]
    assert isinstance(cause_inner, TypeVar)
    assert cause_inner.__name__ == "Cause"
    assert cause_field.wrapper is list

    cause_option = next(iter(cause_field.type_options))
    assert isinstance(cause_option, RelationToTypeVar)
    assert cause_option.type_var_name == "Cause"
    assert isinstance(cause_option.annotated_type, TypeVar)
    assert cause_option.annotated_type.__name__ == "Cause"

    result_field = Causes._meta.fields["result"]
    assert isinstance(result_field, RelationFieldDefinition)
    assert result_field.field_name == "result"
    assert result_field.field_on_model is Causes
    assert get_origin(result_field.annotated_type) is list
    result_inner = get_args(result_field.annotated_type)[0]
    assert isinstance(result_inner, TypeVar)
    assert result_inner.__name__ == "Result"
    assert result_field.wrapper is list

    result_option = next(iter(result_field.type_options))
    assert isinstance(result_option, RelationToTypeVar)
    assert result_option.type_var_name == "Result"
    assert isinstance(result_option.annotated_type, TypeVar)
    assert result_option.annotated_type.__name__ == "Result"


def test_relation_to_conjunction():
    class Statement(Document):
        action: Causes[Task, Incident]

    class Task(Document):
        pass

    class Incident(Document):
        pass

    class Causes[Cause, Result](Conjunction):
        cause: list[Cause]
        result: list[Result]

    class ReallyCauses(Causes):
        pass

    statement_action_field = Statement._meta.fields["action"]
    assert statement_action_field
    assert isinstance(statement_action_field, RelationFieldDefinition)
    assert statement_action_field.field_name == "action"
    assert statement_action_field.field_on_model is Statement
    assert statement_action_field.annotated_type == Causes[Task, Incident]
    assert len(statement_action_field.type_options) == 2

    statement_action_field_type_options = statement_action_field.type_options

    type_option_0 = [
        t
        for t in statement_action_field_type_options
        if isinstance(t, RelationToConjunction) and t.conjunction_type is Causes
    ][0]
    assert isinstance(type_option_0, RelationToConjunction)
    assert type_option_0.annotated_type == Causes[Task, Incident]
    assert type_option_0.edge_model is None
    assert type_option_0.conjunction_type is Causes
    type_options_0_cause = type_option_0.parameter_type_options["Cause"]
    assert type_options_0_cause.type_var_name == "Cause"
    assert type_options_0_cause.type_options == frozenset(
        [RelationToDocument(annotated_type=Task)]
    )
    type_options_0_result = type_option_0.parameter_type_options["Result"]
    assert type_options_0_result.type_var_name == "Result"
    assert type_options_0_result.type_options == frozenset(
        [RelationToDocument(annotated_type=Incident)]
    )

    type_option_1 = [
        t
        for t in statement_action_field_type_options
        if isinstance(t, RelationToConjunction) and t.conjunction_type is ReallyCauses
    ][0]
    assert type_option_1.annotated_type == Causes[Task, Incident]
    assert type_option_1.edge_model is None
    assert type_option_1.conjunction_type is ReallyCauses
    type_options_1_cause = type_option_1.parameter_type_options["Cause"]
    assert type_options_1_cause.type_var_name == "Cause"
    assert type_options_1_cause.type_options == frozenset(
        [RelationToDocument(annotated_type=Task)]
    )
    type_options_1_result = type_option_1.parameter_type_options["Result"]
    assert type_options_1_result.type_var_name == "Result"
    assert type_options_1_result.type_options == frozenset(
        [RelationToDocument(annotated_type=Incident)]
    )


def test_get_fields_basic():
    class Action(Document):
        carried_out_by_person: Person
        carried_out_when: datetime
        carried_out_where: Place

    class Person(Entity):
        pass

    class Place(Entity):
        pass

    assert list(field_name for field_name, _, _, _ in get_fields_on_model(Action)) == [
        "carried_out_by_person",
        "carried_out_when",
        "carried_out_where",
    ]


def test_get_fields_with_overridden():
    class Statement(Document):
        actor: Person
        location: Place

    class Action(Statement):
        carried_out_by_person: Annotated[
            Person,
            RelationConfig(subclasses_parent_fields=[FieldSubclassing("actor")]),
        ]
        carried_out_when: datetime
        carried_out_where: Annotated[
            Place, RelationConfig(subclasses_parent_fields=["location"])
        ]

    class Person(Entity):
        pass

    class Place(Entity):
        pass

    assert list(field_name for field_name, _, _, _ in get_fields_on_model(Action)) == [
        "carried_out_by_person",
        "carried_out_when",
        "carried_out_where",
    ]

    action_carried_out_by_person_field = Action._meta.fields["carried_out_where"]
    assert isinstance(action_carried_out_by_person_field, RelationFieldDefinition)
    assert action_carried_out_by_person_field.subclasses_parent_fields == [
        FieldSubclassing(
            field_name="location",
            field_on_model=Statement,
            subclassed_field_definition=Statement._meta.fields["location"],
        )
    ]


def test_get_fields_with_overridden_raises_error_if_no_such_field():
    with pytest.raises(PanglossModelError):

        class Statement(Document):
            actor: Person

        class Action(Statement):
            carried_out_by_person: Annotated[
                Person,
                RelationConfig(
                    subclasses_parent_fields=[FieldSubclassing("WRONG_FIELD_NAME")]
                ),
            ]

        class Person(Entity):
            pass

        class Place(Entity):
            pass


def test_subclass_raises_error_if_type_not_narrowed():
    with pytest.raises(PanglossModelError):

        class Statement(Document):
            actor: Person

        class Action(Statement):
            carried_out_by_person: Annotated[
                Place,
                RelationConfig(subclasses_parent_fields=[FieldSubclassing("actor")]),
            ]

        class Person(Entity):
            pass

        class Dude(Person):
            pass

        class Place(Entity):
            pass


def test_subclass_does_not_raise_error_with_subtype():
    class Person(Entity):
        pass

    class Statement(Document):
        actor: Person

    class Action(Statement):
        carried_out_by_person: Annotated[
            Dude,
            RelationConfig(subclasses_parent_fields=[FieldSubclassing("actor")]),
        ]

    class Dude(Person):
        pass


def test_fields_on_heritable_trait():
    class Agent(Trait):
        name: str

    assert Agent._meta.fields
    agent_name_field = Agent._meta.fields["name"]
    assert agent_name_field
    assert isinstance(agent_name_field, LiteralFieldDefinition)
    assert agent_name_field.field_name == "name"
    assert agent_name_field.field_on_model is Agent
    assert agent_name_field.annotated_type is str


def test_fields_on_non_heritable_trait():
    class Agent(NonHeritableTrait):
        name: str

    assert Agent._meta.fields
    agent_name_field = Agent._meta.fields["name"]
    assert agent_name_field
    assert isinstance(agent_name_field, LiteralFieldDefinition)
    assert agent_name_field.field_name == "name"
    assert agent_name_field.field_on_model is Agent
    assert agent_name_field.annotated_type is str


def test_inheritance_from_trait():
    class Agent(Trait):
        name: str

    class SubAgent(Agent):
        number: int

    class Person(Entity, SubAgent):
        _meta = Entity.Meta()

    class Group(Entity, Agent):
        _meta = Entity.Meta()

    class Statement(Document):
        _meta = Document.Meta(abstract=True)

    class Action(Statement):
        pass

    assert Agent._meta._owner_class is Agent
    assert SubAgent._meta._owner_class is SubAgent

    assert SubAgent._meta.fields["name"] == LiteralFieldDefinition(
        field_on_model=SubAgent, field_name="name", annotated_type=str
    )

    assert Person._meta.fields["name"] == LiteralFieldDefinition(
        field_on_model=Person, field_name="name", annotated_type=str
    )


def test_subclassing_field_from_heritable_trait():

    class Dude(Entity):
        pass

    class Statement(Document):
        pass

    class WithPrimaryAgent(Trait):
        primary_agent: Dude

    class Action(Statement, WithPrimaryAgent):
        carried_out_by_person: Annotated[
            Dude,
            RelationConfig(
                subclasses_parent_fields=[FieldSubclassing("primary_agent")]
            ),
        ]

    assert "primary_agent" not in Action._meta.fields

    action_carried_out_by_person_field = Action._meta.fields["carried_out_by_person"]
    assert isinstance(action_carried_out_by_person_field, RelationFieldDefinition)
    assert action_carried_out_by_person_field.subclasses_parent_fields == [
        FieldSubclassing(
            field_name="primary_agent",
            field_on_model=WithPrimaryAgent,
            subclassed_field_definition=WithPrimaryAgent._meta.fields["primary_agent"],
        )
    ]


def test_subclass_inheriting_from_non_heritable_trait():
    class Purchaseable(NonHeritableTrait):
        amount: int

    class Dog(Entity, Purchaseable):
        pass

    class Beagle(Dog):
        pass

    class SuperBeagle(Beagle):
        pass

    assert get_all_parent_classes(Dog) == [Purchaseable]
    assert get_all_parent_classes(Beagle) == [Dog, Purchaseable]
    assert get_all_parent_classes(model=SuperBeagle) == [Beagle, Dog, Purchaseable]

    # Check Dog does have "amount" field as it inherits directly from Purchaseable
    assert Dog._meta.fields["amount"]

    # Check Beagle and SuperBeagle do not have "amont" field as not directly
    # inheriting from Purchaseable
    assert "amount" not in Beagle._meta.fields

    assert "amount" not in SuperBeagle._meta.fields


def test_field_required_to_fulfil_inherited_field():
    class Person(Entity):
        pass

    class Place(Entity):
        pass

    class PersonInLocation(Document):
        person: Person
        place: Place

    class Statement(Document):
        pass

    class Action(Document, Fulfils[PersonInLocation]):
        pass

    action_person_field = Action._meta.fields["person"]
    assert isinstance(action_person_field, RelationFieldDefinition)
    assert action_person_field.field_required_to_fulfil == [
        FieldFulfilment(field_name="person", fulfils_class=PersonInLocation)
    ]

    action_place_field = Action._meta.fields["place"]
    assert isinstance(action_place_field, RelationFieldDefinition)
    assert action_place_field.field_required_to_fulfil == [
        FieldFulfilment(field_name="place", fulfils_class=PersonInLocation)
    ]

    assert False


def test_field_required_to_fulfil_subclassed_field():
    class Person(Entity):
        pass

    class Place(Entity):
        pass

    class PersonInLocation(Document):
        person: Person
        place: Place

    class Statement(Document):
        pass

    class Action(Document, Fulfils[PersonInLocation]):
        person_carrying_out_action: Annotated[
            Person, RelationConfig(subclasses_parent_fields=["person"])
        ]
