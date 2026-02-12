from pytest import raises

from pangloss.exceptions import PanglossInitialisationError
from pangloss.model_setup.model_manager import ModelManager
from pangloss.models import (
    Conjunction,
    Document,
    EdgeModel,
    Embedded,
    Entity,
    HeritableTrait,
    NonHeritableTrait,
    ReifiedRelation,
    ReifiedRelationDocument,
    SemanticSpace,
    SubDocument,
)


def test_model_manager_cannot_be_initialised_or_subclassed():

    with raises(PanglossInitialisationError):
        ModelManager()

    with raises(PanglossInitialisationError):

        class NotAllowedSubclassing(ModelManager):
            pass


def test_register_models_with_model_manager():

    class Factoid(Document):
        pass

    class Statement(SubDocument):
        pass

    class Agent(HeritableTrait):
        pass

    class Purchaseable(NonHeritableTrait):
        pass

    class Person(Entity):
        pass

    class Identification[Target](ReifiedRelation[Target]):
        pass

    class WithProxy[Target, Proxy](ReifiedRelationDocument[Target]):
        proxy: list[Proxy]

    class Dating(Embedded):
        pass

    class Negative(SemanticSpace):
        pass

    class BecauseOfXThenY(Conjunction):
        pass

    class Certainty(EdgeModel):
        pass

    assert ModelManager._documents == {"Factoid": Factoid}
    assert ModelManager._subdocuments == {"Statement": Statement}
    assert ModelManager._heritable_traits == {"Agent": Agent}
    assert ModelManager._non_heritable_traits == {"Purchaseable": Purchaseable}
    assert ModelManager._entities == {"Person": Person}
    assert ModelManager._reified_relations == {"Identification": Identification}
    assert ModelManager._reified_relation_documents == {"WithProxy": WithProxy}
    assert ModelManager._embedded == {"Dating": Dating}
    assert ModelManager._semantic_spaces == {"Negative": Negative}
    assert ModelManager._conjunctions == {"BecauseOfXThenY": BecauseOfXThenY}
    assert ModelManager._edge_models == {"Certainty": Certainty}
