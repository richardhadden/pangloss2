from typing import ClassVar

from pydantic import BaseModel, ConfigDict, Field
from pydantic_meta_kit import InheritValue

from pangloss.model_setup.field_definitions import FieldDefinition, ModelFields
from pangloss.model_setup.model_bases.base_object import _DeclaredClass


class ReifiedRelationMeta(BaseModel):
    _owner_class: type[ReifiedRelation] | InheritValue = InheritValue.AS_DEFAULT

    field_definitions: ModelFields = Field(default_factory=ModelFields)

    @property
    def fields(self) -> dict[str, FieldDefinition]:
        return self.field_definitions.fields


class ReifiedRelation[TTarget](_DeclaredClass):
    model_config = ConfigDict(validate_assignment=True)

    _meta: ClassVar[ReifiedRelationMeta] = ReifiedRelationMeta()  # pyright: ignore[reportIncompatibleVariableOverride]

    target: list[TTarget]

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs) -> None:

        if cls is ReifiedRelation:
            return

        cls._initialised = False

        # Make sure _meta class is new and not inherited
        cls._meta = cls.__dict__.get("_meta", ReifiedRelationMeta())  # pyright: ignore[reportIncompatibleVariableOverride]

        # Set owner class on cls._meta
        cls._meta._owner_class = cls

        from pangloss.model_setup.model_manager import ModelManager

        ModelManager.register_reified_relation(cls)
        ModelManager.try_initialise_all_models(cls)


class ReifiedRelationDocument[Target](_DeclaredClass):
    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs) -> None:

        if cls is ReifiedRelation:
            return

        from pangloss.model_setup.model_manager import ModelManager

        ModelManager.register_reified_relation_document(cls)

        ModelManager.try_initialise_all_models(cls)

    target: Target
