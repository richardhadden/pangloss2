from typing import Literal
from uuid import UUID

from pydantic import AnyHttpUrl

from pangloss.model_setup.model_bases.entity import Entity


def test_reference_set_on_entities():
    class Person(Entity):
        pass

    assert Person.ReferenceSet
    assert Person.ReferenceSet.model_fields["type"].annotation == Literal["Person"]
    assert Person.ReferenceSet.model_fields["id"].annotation == UUID | AnyHttpUrl
