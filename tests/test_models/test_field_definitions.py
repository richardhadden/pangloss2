from pytest import raises

from pangloss.exceptions import PanglossInitialisationError
from pangloss.model_setup.model_manager import ModelManager
from pangloss.models import Document, HeritableTrait, NonHeritableTrait, SubDocument


def test_model_manager():

    with raises(PanglossInitialisationError):
        ModelManager()

    with raises(PanglossInitialisationError):

        class NotAllowedSubclassing(ModelManager):
            pass

    class Factoid(Document):
        pass

    class Statement(SubDocument):
        pass

    class Agent(HeritableTrait):
        pass

    class Purchaseable(NonHeritableTrait):
        pass

    assert ModelManager._documents == {"Factoid": Factoid}
    assert ModelManager._subdocuments == {"Statement": Statement}
    assert ModelManager._heritable_traits == {"Agent": Agent}
    assert ModelManager._non_heritable_traits == {"Purchaseable": Purchaseable}
