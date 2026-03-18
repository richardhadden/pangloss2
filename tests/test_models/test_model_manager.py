from pytest import raises

from pangloss.exceptions import PanglossInitialisationError
from pangloss.model_setup.model_bases.annotated_value import AnnotatedValue
from pangloss.model_setup.model_bases.base_types import BaseTypes
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

    class Statement(Document):
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

    class Negative[Content](SemanticSpace[Content]):
        pass

    class BecauseOfXThenY(Conjunction):
        pass

    class Certainty(EdgeModel):
        pass

    class WithCertainty[T: type[BaseTypes]](AnnotatedValue[T]):
        pass

    assert ModelManager._documents == {"Factoid": Factoid, "Statement": Statement}

    assert ModelManager._heritable_traits == {"Agent": Agent}
    assert ModelManager._non_heritable_traits == {"Purchaseable": Purchaseable}
    assert ModelManager._entities == {"Person": Person}
    assert ModelManager._reified_relations == {"Identification": Identification}
    assert ModelManager._reified_relation_documents == {"WithProxy": WithProxy}
    assert ModelManager._embedded == {"Dating": Dating}
    assert ModelManager._semantic_spaces == {"Negative": Negative}
    assert ModelManager._conjunctions == {"BecauseOfXThenY": BecauseOfXThenY}
    assert ModelManager._edge_models == {"Certainty": Certainty}
    assert ModelManager._annotated_values == {"WithCertainty": WithCertainty}
