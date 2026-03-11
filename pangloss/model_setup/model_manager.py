"""ModelManager and related helpers.

This module provides a central registry of all Pangloss model types and
coordinates deferred initialisation of models once their dependencies are
registered.
"""

from collections import ChainMap
from typing import TYPE_CHECKING, Any, no_type_check

from pydantic import PydanticUndefinedAnnotation

from pangloss.exceptions import (
    PanglossInitialisationError,
)
from pangloss.model_setup.initialise_field_definitions import (
    initialise_field_definitions,
)
from pangloss.model_setup.model_bases.base_object import _DeclaredClass

if TYPE_CHECKING:
    from pangloss.models import (
        AnnotatedValue,
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
    )

type ModelTypes = (
    Conjunction
    | Document
    | EdgeModel
    | Embedded
    | Entity
    | HeritableTrait
    | NonHeritableTrait
    | ReifiedRelation
    | ReifiedRelationDocument
    | Relation
    | SemanticSpace
)

type IntialisationTypes = (
    Conjunction
    | Document
    | Embedded
    | Entity
    | HeritableTrait
    | NonHeritableTrait
    | ReifiedRelation
    | SemanticSpace
)


class ClassPropertyDescriptor(object):
    """Descriptor enabling class-level properties with optional setters.

    This allows defining attributes that behave like properties when accessed
    on the class itself (rather than on an instance), including a setter.
    """

    def __init__(self, fget, fset=None):
        self.fget = fget
        self.fset = fset

    def __get__(self, obj, klass=None):
        if klass is None:
            klass = type(obj)
        return self.fget.__get__(obj, klass)()

    def __set__(self, obj, value):
        if not self.fset:
            raise AttributeError("can't set attribute")
        type_ = type(obj)
        return self.fset.__get__(obj, type_)(value)

    def setter(self, func):
        if not isinstance(func, (classmethod, staticmethod)):
            func = classmethod(func)
        self.fset = func
        return self


class ClassPropertyMetaClass(type):
    def __setattr__(self, key, value):
        if key in self.__dict__:
            obj: Any | None = self.__dict__.get(key)
        else:
            raise Exception()
        if obj and type(obj) is ClassPropertyDescriptor:
            return obj.__set__(self, value)

        return super(ClassPropertyMetaClass, self).__setattr__(key, value)


def classproperty(func):
    """Create a class-level property.

    Similar to @property, but the property is accessed via the class.
    """

    if not isinstance(func, (classmethod, staticmethod)):
        func = classmethod(func)
    return ClassPropertyDescriptor(func)


class ModelManager(metaclass=ClassPropertyMetaClass):
    """Central registry and initialisation coordinator for Pangloss models.

    Models register themselves with ModelManager as they are declared. This
    allows deferred initialisation of model field definitions once all
    required types are available.
    """

    def __init__(self) -> None:
        raise PanglossInitialisationError("ModelManager cannot be initialised")

    def __init_subclass__(cls) -> None:
        raise PanglossInitialisationError("ModelManager cannot be subclassed")

    _documents: dict[str, type[Document]] = {}

    _entities: dict[str, type[Entity]] = {}
    _heritable_traits: dict[str, type[HeritableTrait]] = {}
    _non_heritable_traits: dict[str, type[NonHeritableTrait]] = {}
    _embedded: dict[str, type[Embedded]] = {}
    _reified_relations: dict[str, type[ReifiedRelation]] = {}
    _reified_relation_documents: dict[str, type[ReifiedRelationDocument]] = {}
    _semantic_spaces: dict[str, type[SemanticSpace]] = {}
    _conjunctions: dict[str, type[Conjunction]] = {}
    _relations: dict[str, type[Relation]] = {}
    _edge_models: dict[str, type[EdgeModel]] = {}
    _annotated_values: dict[str, type[AnnotatedValue]] = {}

    @classmethod
    @no_type_check
    def all_models(cls) -> ChainMap[str, type[_DeclaredClass]]:
        """Return a mapping of every registered model type by class name."""

        return ChainMap(
            cls._documents,
            cls._entities,
            cls._heritable_traits,
            cls._non_heritable_traits,
            cls._embedded,
            cls._reified_relations,
            cls._reified_relation_documents,
            cls._semantic_spaces,
            cls._conjunctions,
            cls._relations,
            cls._edge_models,
            cls._annotated_values,
        )

    @classmethod
    @no_type_check
    def initialisable_models(cls) -> ChainMap[str, type[_DeclaredClass]]:
        """Return models that should be initialised (registered types)."""

        return ChainMap(
            cls._documents,
            cls._entities,
            cls._heritable_traits,
            cls._non_heritable_traits,
            cls._embedded,
            cls._reified_relations,
            cls._reified_relation_documents,
            cls._semantic_spaces,
            cls._conjunctions,
            cls._relations,
            cls._edge_models,
            cls._annotated_values,
        )

    @classmethod
    def _reset(cls) -> None:
        """Reset all registries to an empty state.

        Primarily used for testing to ensure a clean slate between runs.
        """

        cls._documents: dict[str, type[Document]] = {}
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
        cls._annotated_values: dict[str, type[AnnotatedValue]] = {}

    @classmethod
    def register_document(cls, model: type[Document]):
        """Register a document model class.

        Document classes are a core model type in Pangloss and are tracked so that
        their field definitions can be initialised when all types are available.
        """

        cls._documents[model.__name__] = model

    @classmethod
    def register_entity(cls, model: type[Entity]):
        """Register an entity model class."""

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
        print("Registering", model)

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
    def register_annotated_value(cls, model: type[AnnotatedValue]):
        generic_metadata = model.__pydantic_generic_metadata__

        if not generic_metadata["args"]:
            cls._annotated_values[model.__name__] = model

    @classmethod
    def try_initialise_all_models(cls, declared_class):
        """Attempt to initialise any models that have all dependencies declared.

        This method is invoked each time a new model is registered. It will:

        1. Attempt to rebuild each registered model, allowing Pydantic to resolve
           forward references once all types are available.
        2. If every model is complete, initialise field definitions for any models
           that have not yet been initialised.

        Models that are still missing dependencies are left untouched and will be
        revisited when additional types are registered.
        """

        # Go through all models and try to rebuild, which will succeed is all
        # dependencies have also been declared; otherwise, wait for more models
        # to be declared
        for model in cls.all_models().values():
            print(model.__name__)
            if not model.__pydantic_complete__:
                try:
                    model.model_rebuild(_types_namespace=cls.all_models())
                except PydanticUndefinedAnnotation:
                    pass

        # Check all models so far have no undeclared dependencies; otherwise, return
        if not all(model.__pydantic_complete__ for model in cls.all_models().values()):
            return

        # Get models that have not been initialised
        uninitialised_models = [
            model
            for model in cls.all_models().values()
            if hasattr(model, "_initialised")
            and not getattr(model, "_initialised", False)
        ]

        for model in uninitialised_models:
            initialise_field_definitions(model)
            model._initialised = True

        # If the current declared_class is a subclass of something else
        # that is a dependency of a class already declared, we need to rebuild
        # the model fields for that class so that the subclass is taken into account
        for model in cls.all_models().values():
            for kls in model.depends_on_classes:
                if issubclass(declared_class, kls):
                    initialise_field_definitions(model)
                    break
