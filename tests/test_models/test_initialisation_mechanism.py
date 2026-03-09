from pangloss.model_setup.model_bases.document import Document
from pangloss.model_setup.model_bases.entity import Entity


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

    # assert Factoid.model_fields["statements"].annotation is Statement
    # assert Statement.model_fields["concerns_dog"].annotation is Dog
