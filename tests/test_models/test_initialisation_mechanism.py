from pangloss.model_setup.model_bases.document import Document
from pangloss.model_setup.model_bases.entity import Entity
from pangloss.model_setup.model_bases.sub_document import SubDocument


def test_initialisation_completes_eventually():
    """Tests that a model on __pydantic_init_subclass__ registers
    itself, calls ModelManager.initialise_models()"""

    class Dog(Entity):
        pass

    class Factoid(Document):
        name: str
        statements: Statement

    class Statement(SubDocument):
        concerns_dog: Dog

    assert Factoid._meta._owner_class is Factoid
    assert Factoid._initialised is True

    assert Factoid.model_fields["statements"].annotation is Statement
    assert Statement.model_fields["concerns_dog"].annotation is Dog
