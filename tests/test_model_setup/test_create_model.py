from typing import Literal, no_type_check
from uuid import UUID, uuid7

import pytest
from pydantic import AnyHttpUrl, ValidationError

from pangloss.model_setup.field_definitions import RelationFieldDefinition
from pangloss.model_setup.model_bases.document import Document
from pangloss.model_setup.model_bases.entity import Entity
from pangloss.model_setup.model_bases.reified_relation import ReifiedRelation


@no_type_check
def test_camel_case():
    class Statement(Document):
        some_snake: str

    st = Statement.Create(**dict(label="A statement", someSnake="hello"))
    assert st.some_snake == "hello"


@no_type_check
def test_meta_accessible_through_create():
    class Statement(Document):
        some_snake: str

    assert Statement.Create._meta is Statement._meta


@no_type_check
def test_type_field_is_correct():
    class Statement(Document):
        pass

    assert Statement.Create.model_fields["type"].annotation == Literal["Statement"]


@no_type_check
def test_create_model_for_document_with_no_id():
    class Statement(Document):
        pass

    assert Statement.Create

    assert Statement.Create._owner is Statement

    assert "id" not in Statement.Create.model_fields

    st = Statement.Create(label="A Statement")
    assert st.label == "A Statement"


@no_type_check
def test_create_model_for_document_with_id_allowed():
    class Statement(Document):
        _meta = Document.Meta(create_with_id=True)

    assert Statement.Create
    assert "id" in Statement.Create.model_fields

    id_field = Statement.Create.model_fields["id"]

    assert id_field.annotation == UUID | None

    st = Statement.Create(id=uuid7(), create_new=True, label="A Statement")
    assert isinstance(st.id, UUID)
    assert st.create_new
    assert st.label == "A Statement"


@no_type_check
def test_create_model_for_document_with_id_and_url_allowed_and_no_label():
    class Statement(Document):
        _meta = Document.Meta(
            create_with_id=True, accept_url_as_id=True, require_label=False
        )

    assert Statement.Create
    assert "id" in Statement.Create.model_fields

    id_field = Statement.Create.model_fields["id"]

    assert id_field.annotation == UUID | AnyHttpUrl | None

    st = Statement.Create(
        id="http://test.com/statement1",
        create_new=True,
    )
    assert isinstance(st.id, AnyHttpUrl)
    assert st.create_new


@no_type_check
def test_create_model_for_entity():
    class Person(Entity):
        pass

    assert Person.Create

    assert "id" not in Person.Create.model_fields
    assert "label" in Person.Create.model_fields


@no_type_check
def test_create_model_for_entity_with_id():
    class Person(Entity):
        _meta = Entity.Meta(create_with_id=True)

    assert Person.Create

    assert "id" in Person.Create.model_fields
    assert Person.Create.model_fields["id"].annotation == UUID | AnyHttpUrl | None
    assert "label" in Person.Create.model_fields

    p = Person.Create(id=uuid7(), label="John Smith", create_new=True)
    assert p.id

    # With an ID provided, create_new=True must also be set
    with pytest.raises(ValidationError):
        Person.Create(id="http://mything.net/person", label="Toby Jones")

    # With create_new=True set, an ID must also be provided
    with pytest.raises(ValidationError):
        Person.Create(label="Toby Jones", create_new=True)


@no_type_check
def test_typevar_fields():

    class WithProxy[TTarget, TProxy](ReifiedRelation[TTarget]):
        proxy: list[Identification[TProxy]]

    class Identification[TTarget](ReifiedRelation[TTarget]):
        pass

    with_proxy_proxy_field_definition = WithProxy._meta.fields["proxy"]
    assert isinstance(with_proxy_proxy_field_definition, RelationFieldDefinition)
    assert with_proxy_proxy_field_definition.contains_typevar is True

    assert list(WithProxy._meta.fields.typevar_fields.keys()) == ["target", "proxy"]


@no_type_check
def test_build_base_create_model_for_reified_relation():

    class Identification[TTarget](ReifiedRelation[TTarget]):
        pass

    assert "id" not in Identification.Create.model_fields


@no_type_check
def test_add_fields_to_document_create_model():
    class Statement(Document):
        name: str
        age: int
        numbers: list[int]

    assert "name" in Statement.Create.model_fields
    name_field = Statement.Create.model_fields["name"]
    assert name_field.annotation is str

    assert "age" in Statement.Create.model_fields
    age_field = Statement.Create.model_fields["age"]
    assert age_field.annotation is int

    assert "numbers" in Statement.Create.model_fields
    numbers_field = Statement.Create.model_fields["numbers"]
    assert numbers_field.annotation == list[int]

    st = Statement.Create(label="A Statement", name="John", age=12, numbers=[1, 2, 3])
    assert st.label == "A Statement"
    assert st.name == "John"
    assert st.age == 12
    assert st.numbers == [1, 2, 3]

    with pytest.raises(ValidationError):
        st = Statement.Create(label="A Statement", name="John", age=12, numbers="WRONG")


@no_type_check
def test_add_simple_relation_to_document():
    class Statement(Document):
        was_carried_out_by: Person

    class Person(Entity):
        pass
