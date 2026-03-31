from typing import Literal
from uuid import UUID

from pydantic import AnyHttpUrl

from pangloss.model_setup.model_bases.edge_model import EdgeModel
from pangloss.model_setup.model_bases.entity import Entity


def test_reference_set_on_entities():
    class Person(Entity):
        pass

    assert Person.ReferenceSet
    assert Person.ReferenceSet.model_fields["type"].annotation == Literal["Person"]
    assert Person.ReferenceSet.model_fields["id"].annotation == UUID | AnyHttpUrl


def test_reference_set_with_edge_property():
    class Person(Entity):
        pass

    class Certainty(EdgeModel):
        certainty: int

    assert Person.ReferenceSet

    assert Person.ReferenceSet.model_fields["type"].annotation == Literal["Person"]

    assert Person.ReferenceSet.apply_edge_model(Certainty)

    assert issubclass(Person.ReferenceSet._via.Certainty, Person.ReferenceSet)

    assert (
        Person.ReferenceSet._via.Certainty.__name__ == "PersonReferenceSetViaCertainty"
    )

    assert (
        Person.ReferenceSet._via.Certainty.model_fields["edge_properties"].annotation
        is Certainty
    )

    assert (
        Person.ReferenceSet._via.Certainty.model_fields["type"].annotation
        == Literal["Person"]
    )
