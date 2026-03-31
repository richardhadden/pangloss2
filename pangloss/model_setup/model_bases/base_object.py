from abc import ABC, abstractmethod
from functools import cache
from typing import TYPE_CHECKING, ClassVar, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, PrivateAttr, create_model
from pydantic.alias_generators import to_camel

if TYPE_CHECKING:
    from pangloss.model_setup.field_definitions import (
        FieldDefinition,
        ModelFieldDict,
        ModelFields,
    )
    from pangloss.model_setup.model_bases.edge_model import EdgeModel


class _BaseObject(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True, alias_generator=to_camel, populate_by_name=True
    )

    _initialised: ClassVar[bool] = False


class DeclaredClassMeta(ABC):
    @property
    @abstractmethod
    def fields(self) -> ModelFieldDict[str, FieldDefinition]: ...

    field_definitions: ModelFields


class _DeclaredClass(_BaseObject):
    _meta: ClassVar[DeclaredClassMeta]
    _depends_on_classes: ClassVar[set[type[_DeclaredClass]]] = PrivateAttr()

    @classmethod
    def __pydantic_init_subclass__(cls, **_):
        cls._depends_on_classes = set()


class MetaGetter:
    """Descriptor class for getting the _meta class from
    the _DeclaredClass of an _ActionClass"""

    def __get__(self, instance, owner):
        return owner._owner._meta


class GetItemViaAttrDict[T](dict):
    def __getattr__(self, name) -> type[T]:
        if name in self:
            return self[name]
        return super().__getattribute__(name)


class _ActionClass(_BaseObject):
    _owner: ClassVar[type[_DeclaredClass]]
    _meta: ClassVar = MetaGetter()
    _via: ClassVar[GetItemViaAttrDict[Self]] = GetItemViaAttrDict()

    @classmethod
    @cache
    def apply_edge_model(cls, edge_model: type[EdgeModel]):
        """Creates a variant of the model with additional 'edge_property' field
        of the type supplied"""
        model = create_model(
            f"{cls.__name__}Via{edge_model.__name__}",
            __base__=cls,
            edge_properties=edge_model,
        )
        cls._via[edge_model.__name__] = model
        return model


class _ReferenceViewBase(_ActionClass):
    id: UUID
    label: str


class _ReferenceSetBase(_ActionClass):
    id: UUID


class _CreateBase(_ActionClass):
    pass


class _ViewBase(_ActionClass):
    id: UUID


class _UpdateBase(_ActionClass):
    id: UUID
