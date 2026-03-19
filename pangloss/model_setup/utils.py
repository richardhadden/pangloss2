from functools import cache
from inspect import isclass
from types import UnionType
from typing import Any, get_args, overload

from pangloss.model_setup.model_bases.base_object import _DeclaredClass
from pangloss.model_setup.model_bases.conjunction import Conjunction
from pangloss.model_setup.model_bases.document import Document
from pangloss.model_setup.model_bases.embedded import Embedded
from pangloss.model_setup.model_bases.entity import Entity
from pangloss.model_setup.model_bases.reified_relation import (
    ReifiedRelation,
    ReifiedRelationDocument,
)
from pangloss.model_setup.model_bases.semantic_space import SemanticSpace
from pangloss.model_setup.model_bases.trait import (
    HeritableTrait,
    NonHeritableTrait,
    _Trait,
)

type ConcreteUnionType[T] = type[type[T] | type[T]]


@overload
def get_concrete_types[T](
    model: ConcreteUnionType[T], include_abstract: bool = False
) -> set[type[T]]: ...


@overload
def get_concrete_types(
    model: type[Entity],
    include_abstract: bool = False,
) -> set[type[Entity]]: ...


@overload
def get_concrete_types(
    model: type[Document],
    include_abstract: bool = False,
) -> set[type[Document]]: ...


@overload
def get_concrete_types(
    model: type[Embedded],
    include_abstract: bool = False,
) -> set[type[Embedded]]: ...


@overload
def get_concrete_types(
    model: type[SemanticSpace], include_abstract: bool = False
) -> set[type[SemanticSpace]]: ...


@overload
def get_concrete_types(
    model: type[Conjunction], include_abstract: bool = False
) -> set[type[Conjunction]]: ...


@overload
def get_concrete_types(
    model: type[HeritableTrait | NonHeritableTrait],
    include_abstract: bool = False,
) -> set[type[Document]] | set[type[Entity]]: ...


def get_concrete_types(
    model: Any,
    include_abstract: bool = False,
):
    """Return concrete (non-abstract) subclasses for a model.

    This is a convenience wrapper around :func:`generic_get_subclasses` that
    includes the model itself when it is concrete (or when
    ``include_abstract=True``).

    Args:
        model: A Pangloss model class (Document, Entity or Trait).
        include_abstract: If True, include abstract base classes in the result.

    Returns:
        A set of concrete subclasses (and possibly the model itself).
    """

    concrete_types = []
    if isinstance(model, UnionType):
        for type_in_union in get_args(model):
            concrete_types.extend(
                get_concrete_types(type_in_union, include_abstract=include_abstract)
            )

    if isclass(model) and issubclass(
        model, (Document, Entity, Embedded, SemanticSpace, Conjunction)
    ):
        if not model._meta.abstract or include_abstract:
            concrete_types.append(model)
        concrete_types.extend(
            generic_get_subclasses(model, include_abstract=include_abstract)
        )
    return set(concrete_types)


def generic_get_subclasses[
    T: Document | Entity | Embedded | SemanticSpace | Conjunction
](model: type[T], include_abstract: bool = False) -> set[type[T]]:
    """Recursively find subclasses of a Document or Entity model.

    Traverses the subclass tree and returns all reachable subclasses, optionally
    filtering out abstract models.

    Args:
        model: The base class to inspect.
        include_abstract: If False, exclude models whose ``_meta.abstract`` is True.

    Returns:
        A set of subclass types.
    """
    subclasses = []
    for subclass in model.__subclasses__():
        # Skip if it is a parameterised generic
        if subclass.__pydantic_generic_metadata__["origin"] is not None:
            continue

        if not subclass._meta.abstract or include_abstract:
            subclasses += [
                subclass,
                *generic_get_subclasses(subclass, include_abstract=include_abstract),
            ]
        else:
            subclasses += generic_get_subclasses(
                subclass, include_abstract=include_abstract
            )
    return set(subclasses)


def model_is_trait(
    cls: type[_DeclaredClass] | type[HeritableTrait] | type[NonHeritableTrait],
):
    """Determines whether a model is a Trait, or subclass of a Trait,
    rather than a _DeclaredClass type to which a Trait has been applied"""

    return (
        isclass(cls)
        and issubclass(cls, (HeritableTrait, NonHeritableTrait))
        and is_subclass_of_heritable_trait(cls)
    )


def is_subclass_of_heritable_trait(
    cls: type[HeritableTrait] | type[NonHeritableTrait],
) -> bool:
    """Determine whether a class is a subclass of a Trait,
    not the application of a trait to a real Document or Entity class.

    This should work by not having BaseNode in its class hierarchy
    """
    for parent in cls.mro()[1:]:
        if issubclass(parent, (Document, Entity)):
            return False
    else:
        return True


def get_trait_subclasses(
    trait: type[HeritableTrait] | type[NonHeritableTrait],
) -> set[type[HeritableTrait] | type[NonHeritableTrait]]:
    """Get subclasses of a Trait that are Traits, not instantiations
    of a Trait"""

    subclasses = [trait]
    for subclass in trait.__subclasses__():
        if model_is_trait(subclass):
            subclasses.extend(get_trait_subclasses(subclass))
    return set(subclasses)


def get_direct_instantiations_of_trait(
    trait: type[HeritableTrait] | type[NonHeritableTrait],
    follow_trait_subclasses: bool = False,
):
    """Given a Trait class, find the models to which it is *directly* applied,
    i.e. omitting children"""

    if follow_trait_subclasses:
        trait_subclasses = [
            trait_subclass for trait_subclass in get_trait_subclasses(trait)
        ]
        instantiations_of_trait = []
        for trait_subclass in trait_subclasses:
            instantiations_of_trait.extend(
                subclass
                for subclass in trait_subclass.__subclasses__()
                if issubclass(subclass, (Document, Entity))
            )
        return set(instantiations_of_trait)

    return set(
        [
            subclass
            for subclass in trait.__subclasses__()
            if issubclass(subclass, (Document, Entity))
        ]
    )


@cache
def get_usable_declared_classes():
    usable_subclasses: list[type[_DeclaredClass]] = _DeclaredClass.__subclasses__()
    usable_subclasses.remove(_Trait)
    usable_subclasses.extend([HeritableTrait, NonHeritableTrait])
    return set(usable_subclasses)


@overload
def get_parent_class(model: type[Document]) -> type[Document] | None: ...


@overload
def get_parent_class(model: type[Entity]) -> type[Entity] | None: ...


@overload
def get_parent_class(model: type[Embedded]) -> type[Embedded] | None: ...


@overload
def get_parent_class(model: type[ReifiedRelation]) -> type[ReifiedRelation] | None: ...


@overload
def get_parent_class(
    model: type[ReifiedRelationDocument],
) -> type[ReifiedRelationDocument] | None: ...


@overload
def get_parent_class(model: type[SemanticSpace]) -> type[SemanticSpace] | None: ...


@overload
def get_parent_class(model: type[Conjunction]) -> type[Conjunction] | None: ...


@overload
def get_parent_class(
    model: type[HeritableTrait],
) -> type[HeritableTrait] | None: ...


@overload
def get_parent_class(
    model: type[NonHeritableTrait],
) -> type[NonHeritableTrait] | None: ...


@overload
def get_parent_class(
    model: type[_DeclaredClass],
) -> type[_DeclaredClass] | None: ...


def get_parent_class(model) -> Any:
    for parent_class in model.mro():
        if parent_class is model:
            continue
        elif parent_class in get_usable_declared_classes():
            return None
        else:
            return parent_class
    return None


@overload
def get_all_parent_classes(model: type[Document]) -> list[type[Document]]: ...


@overload
def get_all_parent_classes(model: type[Entity]) -> list[type[Entity]]: ...


@overload
def get_all_parent_classes(model: type[Embedded]) -> list[type[Embedded]]: ...


@overload
def get_all_parent_classes(
    model: type[ReifiedRelation],
) -> list[type[ReifiedRelation]]: ...


@overload
def get_all_parent_classes(
    model: type[ReifiedRelationDocument],
) -> list[type[ReifiedRelationDocument]]: ...


@overload
def get_all_parent_classes(
    model: type[SemanticSpace],
) -> list[type[SemanticSpace]]: ...


@overload
def get_all_parent_classes(
    model: type[Conjunction],
) -> list[type[Conjunction]]: ...


@overload
def get_all_parent_classes(
    model: type[HeritableTrait],
) -> list[type[HeritableTrait]]: ...


@overload
def get_all_parent_classes(
    model: type[NonHeritableTrait],
) -> list[type[NonHeritableTrait]]: ...


@overload
def get_all_parent_classes[T: type[_DeclaredClass]](model: T) -> list[T]: ...


def get_all_parent_classes[T: type[_DeclaredClass]](model: T) -> list[T]:
    parent_classes = []
    for parent_class in model.mro():
        if parent_class is model:
            continue
        elif parent_class in get_usable_declared_classes():
            break
        else:
            parent_classes.append(parent_class)

    return parent_classes
