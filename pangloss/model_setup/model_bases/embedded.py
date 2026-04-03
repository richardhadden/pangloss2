from typing import Annotated, ClassVar, Literal

from pydantic import ConfigDict, Field
from pydantic_meta_kit import BaseMeta, InheritValue, MetaRules, WithMeta

from pangloss.model_setup.field_definitions import (
    FieldDefinition,
    ModelFieldDict,
    ModelFields,
)
from pangloss.model_setup.model_bases.base_object import (
    DeclaredClassMeta,
    _CreateBase,
    _DeclaredClass,
)


class EmbeddedMeta(BaseMeta, DeclaredClassMeta):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    _owner_class: type[Embedded] | InheritValue = InheritValue.AS_DEFAULT
    abstract: Annotated[bool, MetaRules.DO_NOT_INHERIT] = False
    require_label: Literal[False] = False
    field_definitions: ModelFields = Field(default_factory=ModelFields)

    @property
    def fields(self) -> ModelFieldDict[str, FieldDefinition]:
        return self.field_definitions.fields


class _EmbeddedCreateBase(_CreateBase):
    pass


class Embedded(_DeclaredClass, WithMeta[EmbeddedMeta]):
    _meta: ClassVar[EmbeddedMeta] = EmbeddedMeta()  # pyright: ignore[reportIncompatibleVariableOverride]

    Create: ClassVar[type[_EmbeddedCreateBase]]

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs) -> None:
        from pangloss.model_setup.model_manager import ModelManager

        cls._initialised = False

        # Make sure _meta class is new and not inherited
        cls._meta = cls.__dict__.get("_meta", EmbeddedMeta())  # pyright: ignore[reportIncompatibleVariableOverride]

        # Set owner class on cls._meta
        cls._meta._owner_class = cls

        ModelManager.register_embedded(cls)
        ModelManager.try_initialise_all_models(cls)
