from typing import Annotated, ClassVar

from pydantic import Field
from pydantic_meta_kit import BaseMeta, InheritValue, MetaRules

from pangloss.model_setup.field_definitions import FieldDefinition, ModelFields
from pangloss.model_setup.model_bases.base_object import (
    DeclaredClassMeta,
    _DeclaredClass,
)


class EmbeddedMeta(BaseMeta, DeclaredClassMeta):
    _owner_class: type[Embedded] | InheritValue = InheritValue.AS_DEFAULT
    abstract: Annotated[bool, MetaRules.DO_NOT_INHERIT] = False
    field_definitions: ModelFields = Field(default_factory=ModelFields)

    @property
    def fields(self) -> dict[str, FieldDefinition]:
        return self.field_definitions.fields


class Embedded(_DeclaredClass):
    _meta: ClassVar[EmbeddedMeta] = EmbeddedMeta()  # pyright: ignore[reportIncompatibleVariableOverride]

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
