import datetime
from typing import Generic

from pydantic import BaseModel
from pydantic_meta_kit import WithMeta

from pangloss.model_setup.model_bases.base_object import _BaseObject, _DeclaredClass
from pangloss.model_setup.model_bases.conjunction import Conjunction
from pangloss.model_setup.model_bases.document import Document, DocumentMeta
from pangloss.model_setup.model_bases.edge_model import EdgeModel
from pangloss.model_setup.model_bases.embedded import Embedded, EmbeddedMeta
from pangloss.model_setup.model_bases.entity import Entity
from pangloss.model_setup.model_bases.reified_relation import (
    ReifiedRelation,
    ReifiedRelationDocument,
)
from pangloss.model_setup.model_bases.relation import Relation
from pangloss.model_setup.model_bases.semantic_space import SemanticSpace
from pangloss.model_setup.model_bases.trait import (
    NonHeritableTrait,
    Trait,
    _Trait,
)
from pangloss.model_setup.utils import (
    generic_get_subclasses,
    get_all_parent_classes,
    get_concrete_types,
    get_direct_instantiations_of_trait,
    get_parent_class,
    get_top_level_classes,
)


def test_get_generic_subclasses():
    class Statement(Document):
        pass

    class Action(Statement):
        pass

    class CreationOfArtwork(Action):
        pass

    class CreationOfPainting(CreationOfArtwork):
        pass

    assert generic_get_subclasses(Statement) == set(
        [Action, CreationOfArtwork, CreationOfPainting]
    )


def test_get_concrete_types_simple():
    class Statement(Document):
        pass

    class Other(Document):
        pass

    class Action(Statement):
        pass

    class CreationOfArtwork(Action):
        _meta = DocumentMeta(abstract=True)

    class CreationOfPainting(CreationOfArtwork):
        pass

    assert get_concrete_types(Statement) == set([Statement, Action, CreationOfPainting])

    assert get_concrete_types(Statement, include_abstract=True) == set(
        [Statement, Action, CreationOfArtwork, CreationOfPainting]
    )

    # Throw in a union type here to check it works
    assert get_concrete_types(Statement | Other) == set(
        [Statement, Action, CreationOfPainting, Other]
    )


def test_get_concrete_types_with_abstract():
    class Statement(Document):
        _meta = DocumentMeta(abstract=True)

    class Thing(Statement):
        pass

    assert get_concrete_types(Statement) == set([Thing])


def test_get_concrete_types_with_abstract_in_union():
    class Statement(Document):
        _meta = DocumentMeta(abstract=True)

    class Thing(Document):
        pass

    assert get_concrete_types(Statement | Thing) == set([Thing])


def test_get_concrete_types_with_embedded_abstract_in_union():
    class Date(Embedded):
        _meta = EmbeddedMeta(abstract=True)
        when: datetime.datetime

    class Statement(Document):
        date: Date

    class SpecialDate(Date):
        pass

    assert get_concrete_types(Date) == set([SpecialDate])
    assert get_concrete_types(SpecialDate) == set([SpecialDate])
    assert get_concrete_types(Date | SpecialDate) == set([SpecialDate])


def test_get_concrete_types_with_semantic_spaces():
    class Negative[Contents](SemanticSpace[Contents]):
        pass

    class ReallyNegative(Negative):
        pass

    assert get_concrete_types(Negative) == set([Negative, ReallyNegative])


def test_get_concrete_types_with_semantic_spaces_does_not_return_parametrised():
    class Negative[Contents](SemanticSpace[Contents]):
        pass

    class ReallyNegative(Negative):
        pass

    class Statement(Document):
        action: Negative[Task]

    class Task(Document):
        pass

    assert get_concrete_types(Negative) == set([Negative, ReallyNegative])


def test_usable_declared_classes():
    assert get_top_level_classes() == set(
        [
            Conjunction,
            Document,
            EdgeModel,
            Embedded,
            Entity,
            ReifiedRelation,
            ReifiedRelationDocument,
            SemanticSpace,
            Relation,
            Trait,
            NonHeritableTrait,
            _BaseObject,
            _DeclaredClass,
            WithMeta,
            _Trait,
            BaseModel,
            object,
            Generic,
        ]
    )


def test_get_parent_class():
    class Statement(Document):
        pass

    class Action(Statement):
        pass

    parent_class = get_parent_class(Action)

    assert parent_class is Statement


def test_get_all_parent_classes():
    class Statement(Document):
        something: int

    class Action(Statement):
        pass

    class Task(Action):
        pass

    assert get_all_parent_classes(Task) == [Action, Statement]


def test_get_all_parent_classes_with_heritable_trait():
    class Statement(Document):
        something: int

    class WithPrimaryAgent(Trait):
        pass

    class Action(Statement, WithPrimaryAgent):
        pass

    class Task(Action):
        pass

    assert get_all_parent_classes(Task) == [Action, Statement, WithPrimaryAgent]


def test_is_subclass_of_heritable_trait():
    class Purchaseable(NonHeritableTrait):
        pass

    class Dog(Entity, Purchaseable):
        pass

    class Beagle(Dog):
        pass

    assert get_direct_instantiations_of_trait(Purchaseable) == {Dog}
