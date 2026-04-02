from typing import Annotated, Any, ClassVar

from pydantic import BaseModel

from pangloss.model_setup.field_definitions import FieldSubclassing
from pangloss.model_setup.model_bases.configs import RelationConfig
from pangloss.model_setup.model_bases.document import Document
from pangloss.model_setup.model_bases.edge_model import EdgeModel
from pangloss.model_setup.model_bases.entity import Entity
from pangloss.model_setup.model_bases.helpers import Fulfils, ViaEdge
from pangloss.models import Conjunction, ReifiedRelation


class Parent:
    pass


class Shortcut(BaseModel):
    name: str
    reverse_name: str
    source: str | type[Parent] | Any
    target_field_objects: str
    Parent: ClassVar[type[Parent]] = Parent


class Certainty(EdgeModel):
    value: int


class Alternative[TAlternativeOption](Conjunction):
    """Expresses a set of options as alternatives, with a given certainty value"""

    option: list[ViaEdge[TAlternativeOption, Certainty]]

    shortcuts: ClassVar[list[Shortcut]] = [
        Shortcut(
            name="is_option_in",
            reverse_name="is_optionally_in",
            source=Shortcut.Parent,
            target_field_objects="option",
        )
    ]


class Identification[TT](ReifiedRelation[TT], Fulfils[Alternative[TT]]):
    """Identifies objects of a type as one of several alternatives, and
    stores the string (e.g. from the source) which identifies the object"""

    target: Annotated[
        list[TT],
        RelationConfig(
            subclasses_parent_fields=[
                FieldSubclassing(field_on_model=Alternative, field_name="option")
            ]
        ),
    ]
    identified_in_text_as: str


class Person(Entity):
    pass


class Place(Entity):
    pass


class Action(Document):
    carried_out_by: list[Identification[Person]]
    """i.e. the source mentions a number of people, which can be identified
    with some probability with one or more actualy people"""

    place_of_action: Alternative[Place]
    """i.e. the source does not mention a place, but we think it could be
    one of a set of places"""
