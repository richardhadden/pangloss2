import warnings
from abc import ABC, abstractmethod
from functools import cache
from typing import TYPE_CHECKING, Any, ClassVar, Self
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    PrivateAttr,
    create_model,
    model_validator,
)
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
    _via: ClassVar[GetItemViaAttrDict[Self]]

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs: Any) -> None:
        cls._via = GetItemViaAttrDict()
        return super().__pydantic_init_subclass__(**kwargs)

    @classmethod
    @cache
    def apply_edge_model(cls, edge_model: type[EdgeModel]) -> type[Self]:
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

    @model_validator(mode="after")
    def remove_label(self):
        """Should not start setting the label of a ReferenceSet,
        but it's allowed as a field as it might be nice sometimes
        to write it in code for clarity"""
        self.label = None
        return self


class _CreateBase(_ActionClass):
    def _to_db_model(self):
        return self._owner.CreateDB(**self.model_dump())  # type: ignore


class _CreateDBBase(_ActionClass):
    def __init__(self, **kwargs):

        # Calling model_construct emits a warning that the data might not be valid,
        # so catch these and supress. This is fine as we later pass the data back to
        # the class.__init__, which will validate it
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            if f := getattr(
                self._owner, "to_db_create", getattr(self._owner, "to_db", None)
            ):
                data = f(self.__class__.model_construct(**kwargs))
                if isinstance(data, dict):
                    super().__init__(**data)
                else:
                    super().__init__(**data.model_dump())
            else:
                super().__init__(**kwargs)


class _ViewBase(_ActionClass):
    id: UUID


class _UpdateBase(_ActionClass):
    id: UUID
