from pangloss.model_setup.model_bases.configs import RelationConfig
from pangloss.model_setup.model_bases.conjunction import Conjunction
from pangloss.model_setup.model_bases.document import Document
from pangloss.model_setup.model_bases.edge_model import EdgeModel
from pangloss.model_setup.model_bases.embedded import Embedded
from pangloss.model_setup.model_bases.entity import Entity
from pangloss.model_setup.model_bases.reified_relation import (
    ReifiedRelation,
    ReifiedRelationDocument,
)
from pangloss.model_setup.model_bases.relation import Relation
from pangloss.model_setup.model_bases.semantic_space import SemanticSpace
from pangloss.model_setup.model_bases.sub_document import SubDocument
from pangloss.model_setup.model_bases.trait import HeritableTrait, NonHeritableTrait

ALL_MODELS = {
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
    Relation,
}
CONFIGS = {RelationConfig}
