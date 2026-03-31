from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, ClassVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, PrivateAttr
from pydantic.alias_generators import to_camel

if TYPE_CHECKING:
    from pangloss.model_setup.field_definitions import (
        FieldDefinition,
        ModelFieldDict,
        ModelFields,
    )


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


class _ActionClass(_BaseObject):
    _owner: ClassVar[type[_DeclaredClass]]
    _meta: ClassVar = MetaGetter()


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
