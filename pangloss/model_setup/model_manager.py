from typing import TYPE_CHECKING

from pangloss.exceptions import PanglossInitialisationError

if TYPE_CHECKING:
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
        Relation,
        SemanticSpace,
        SubDocument,
    )


class ModelManager:
    def __init__(self) -> None:
        raise PanglossInitialisationError("ModelManager cannot be initialised")

    def __init_subclass__(cls) -> None:
        raise PanglossInitialisationError("ModelManager cannot be subclassed")

    _documents: dict[str, type[Document]] = {}
    _subdocuments: dict[str, type[SubDocument]] = {}
    _entities: dict[str, type[Entity]] = {}
    _heritable_traits: dict[str, type[HeritableTrait]] = {}
    _non_heritable_traits: dict[str, type[NonHeritableTrait]] = {}
    _embedded: dict[str, type[Embedded]] = {}
    _reified_relations: dict[str, type[ReifiedRelation]] = {}
    _reified_relation_documents: dict[str, type[ReifiedRelationDocument]]
    _semantic_spaces: dict[str, type[SemanticSpace]]
    _conjunctions: dict[str, type[Conjunction]]
    _relations: dict[str, type[Relation]]
    _edge_models: dict[str, type[EdgeModel]]

    @classmethod
    def _reset(cls) -> None:
        cls._documents: dict[str, type[Document]] = {}
        cls._subdocuments: dict[str, type[SubDocument]] = {}
        cls._entities: dict[str, type[Entity]] = {}
        cls._heritable_traits: dict[str, type[HeritableTrait]] = {}
        cls._non_heritable_traits: dict[str, type[NonHeritableTrait]] = {}
        cls._embedded: dict[str, type[Embedded]] = {}
        cls._reified_relations: dict[str, type[ReifiedRelation]] = {}
        cls._reified_relation_documents: dict[str, type[ReifiedRelationDocument]] = {}
        cls._semantic_spaces: dict[str, type[SemanticSpace]] = {}
        cls._conjunctions: dict[str, type[Conjunction]] = {}
        cls._relations: dict[str, type[Relation]] = {}
        cls._edge_models: dict[str, type[EdgeModel]] = {}

    @classmethod
    def register_document(cls, model: type[Document]):
        cls._documents[model.__name__] = model

    @classmethod
    def register_subdocument(cls, model: type[SubDocument]):
        cls._subdocuments[model.__name__] = model

    @classmethod
    def register_entity(cls, model: type[Entity]):
        cls._entities[model.__name__] = model

    @classmethod
    def register_embedded(cls, model: type[Embedded]):
        cls._embedded[model.__name__] = model

    @classmethod
    def register_heritable_trait(cls, model: type[HeritableTrait]):
        cls._heritable_traits[model.__name__] = model

    @classmethod
    def register_non_heritable_trait(cls, model: type[NonHeritableTrait]):
        cls._non_heritable_traits[model.__name__] = model

    @classmethod
    def register_reified_relation(cls, model: type[ReifiedRelation]):

        generic_metadata = model.__pydantic_generic_metadata__

        if not generic_metadata["args"]:
            cls._reified_relations[model.__name__] = model

    @classmethod
    def register_reified_relation_document(cls, model: type[ReifiedRelationDocument]):

        generic_metadata = model.__pydantic_generic_metadata__

        if not generic_metadata["args"]:
            cls._reified_relation_documents[model.__name__] = model

    @classmethod
    def register_semantic_space(cls, model: type[SemanticSpace]):
        cls._semantic_spaces[model.__name__] = model

    @classmethod
    def register_conjunction(cls, model: type[Conjunction]):
        cls._conjunctions[model.__name__] = model

    @classmethod
    def register_edge_model(cls, model: type[EdgeModel]):
        cls._edge_models[model.__name__] = model

    @classmethod
    def initialise_models(cls):
        from pangloss.model_setup.initialise_meta import initialise_document_meta

        for model_name, model in cls._documents.items():
            initialise_document_meta(model)
