from typing import Any, ClassVar, Self

from pydantic import ConfigDict, Field
from pydantic_meta_kit import BaseMeta, InheritValue

from pangloss.model_setup.field_definitions import (
    FieldDefinition,
    ModelFieldDict,
    ModelFields,
)
from pangloss.model_setup.model_bases.base_object import (
    DeclaredClassMeta,
    _DeclaredClass,
)
from pangloss.model_setup.model_bases.document import Document
from pangloss.model_setup.model_bases.entity import Entity


class TraitMeta[T: Trait | NonHeritableTrait](BaseMeta, DeclaredClassMeta):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    field_definitions: ModelFields = Field(default_factory=ModelFields)
    _owner_class: type[T] | InheritValue = InheritValue.AS_DEFAULT

    @property
    def fields(self) -> ModelFieldDict[str, FieldDefinition]:
        return self.field_definitions.fields


class _Trait(_DeclaredClass):
    # _trait_meta: ClassVar[TraitMeta]
    pass


class Trait[T: Document | Entity](_Trait):
    Meta: ClassVar[Any] = TraitMeta
    # _meta: ClassVar[EntityMeta] = TraitMeta[Self]()  # pyright: ignore[reportAssignmentType, reportIncompatibleVariableOverride]  # ty:ignore[invalid-assignment]
    _meta: Any

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs) -> None:
        from pangloss.model_setup.model_manager import ModelManager

        cls._initialised = False

        # Make sure _meta class is new and not inherited
        cls._meta = TraitMeta[Self]()
        # Set owner class on cls._meta
        cls._meta._owner_class = cls

        ModelManager.register_heritable_trait(cls)
        ModelManager.try_initialise_all_models(cls)


class NonHeritableTrait(_Trait):
    Meta: ClassVar[Any] = TraitMeta
    _meta: Any  # pyright: ignore[reportAssignmentType, reportIncompatibleVariableOverride]  # ty:ignore[invalid-assignment]

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs) -> None:
        from pangloss.model_setup.model_manager import ModelManager

        cls._initialised = False

        # Make sure _meta class is new and not inherited
        cls._meta = cls.__dict__.get("_meta", TraitMeta())  # pyright: ignore[reportIncompatibleVariableOverride]

        # Set owner class on cls._meta
        cls._meta._owner_class = cls  # pyright: ignore[reportAttributeAccessIssue]

        ModelManager.register_non_heritable_trait(cls)
        ModelManager.try_initialise_all_models(cls)
