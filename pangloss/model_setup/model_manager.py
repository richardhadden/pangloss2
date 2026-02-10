from typing import TYPE_CHECKING

from pangloss.exceptions import PanglossInitialisationError

if TYPE_CHECKING:
    from pangloss.models import (
        Document,
        Embedded,
        Entity,
        HeritableTrait,
        NonHeritableTrait,
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

    @classmethod
    def _reset(cls) -> None:
        cls._documents: dict[str, type[Document]] = {}
        cls._subdocuments: dict[str, type[SubDocument]] = {}
        cls._entities: dict[str, type[Entity]] = {}
        cls._heritable_traits: dict[str, type[HeritableTrait]] = {}
        cls._non_heritable_traits: dict[str, type[NonHeritableTrait]] = {}
        cls._embedded: dict[str, type[Embedded]] = {}

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
    def register_heritable_trait(cls, model: type[HeritableTrait]):
        cls._heritable_traits[model.__name__] = model

    @classmethod
    def register_non_heritable_trait(cls, model: type[NonHeritableTrait]):
        cls._non_heritable_traits[model.__name__] = model
