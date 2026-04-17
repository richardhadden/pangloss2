from pangloss.model_setup.model_bases.document import Document
from pangloss.model_setup.model_bases.entity import Entity
from pangloss.model_setup.model_bases.semantic_space import SemanticSpace


def test_initialisation_completes_eventually():
    """Tests that a model on __pydantic_init_subclass__ registers
    itself, calls ModelManager.initialise_models()"""

    class Dog(Entity):
        pass

    class Factoid(Document):
        name: str
        statements: Statement

    class Statement(Document):
        concerns_dog: Dog

    assert Factoid._meta._owner_class is Factoid
    assert Factoid._initialised is True

    assert Statement._meta._owner_class is Statement
    assert Statement._initialised is True

    assert Dog._meta._owner_class is Dog

    assert Factoid.model_fields["statements"].annotation is Statement
    assert Statement.model_fields["concerns_dog"].annotation is Dog


def test_initialisation_of_random_ordered_declaration_1():
    class Negative[T](SemanticSpace[T]):
        pass

    class Factoid(Document):
        statements: list[Negative[Order]]

    class Action(Document):
        pass

    class Order(Document):
        thing_ordered: Subjunctive[Action]

    class Subjunctive[T](SemanticSpace[T]):
        pass

    assert Factoid.Create
