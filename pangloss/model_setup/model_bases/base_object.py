from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, ClassVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict

if TYPE_CHECKING:
    from pangloss.model_setup.field_definitions import FieldDefinition, ModelFields


class _BaseObject(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    _initialised: ClassVar[bool] = False


class DeclaredClassMeta(ABC):
    @property
    @abstractmethod
    def fields(self) -> dict[str, FieldDefinition]: ...

    field_definitions: ModelFields


class _DeclaredClass(_BaseObject):
    _meta: ClassVar[DeclaredClassMeta]
    depends_on_classes: ClassVar[set[type[_DeclaredClass]]]

    @classmethod
    def __pydantic_init_subclass__(cls, **_):
        cls.depends_on_classes = set()


class _ActionClass(_BaseObject):
    _owner: ClassVar[type[_DeclaredClass]]


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
