from typing import ClassVar, cast

from pydantic import Field
from pydantic_meta_kit import BaseMeta, InheritValue

from pangloss.model_setup.field_definitions import (
    ListFieldDefinition,
    LiteralFieldDefinition,
    ModelFields,
)
from pangloss.model_setup.model_bases.base_object import (
    DeclaredClassMeta,
    _DeclaredClass,
)


class EdgeModelMeta(BaseMeta, DeclaredClassMeta):
    _owner_class: type[EdgeModel] | InheritValue = InheritValue.AS_DEFAULT

    field_definitions: ModelFields = Field(default_factory=ModelFields)

    @property
    def fields(self) -> dict[str, LiteralFieldDefinition | ListFieldDefinition]:  # pyright: ignore[reportIncompatibleMethodOverride]
        if self.field_definitions:
            return cast(
                dict[str, LiteralFieldDefinition | ListFieldDefinition],
                self.field_definitions.fields,
            )
        raise Exception(f"{self.__class__.__name__}.field_definition missing")


class EdgeModel(_DeclaredClass):
    _meta: ClassVar[EdgeModelMeta] = EdgeModelMeta()  # pyright: ignore[reportIncompatibleVariableOverride]

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs) -> None:
        from pangloss.model_setup.model_manager import ModelManager

        # Set model it uninitialised, as may inherit _initialised from parent class
        cls._initialised = False

        # Make sure _meta class is new and not inherited
        cls._meta = cls.__dict__.get("_meta", EdgeModelMeta())  # pyright: ignore[reportIncompatibleVariableOverride]

        # Set owner class on cls._meta
        cls._meta._owner_class = cls

        ModelManager.register_edge_model(cls)
        ModelManager.try_initialise_all_models(cls)
