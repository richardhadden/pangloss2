from typing import Annotated, ClassVar

from pydantic import BaseModel, Field
from pydantic_meta_kit import BaseMeta, InheritValue, MetaRules, WithMeta

from pangloss.model_setup.field_definitions import FieldDefinition, ModelFields
from pangloss.model_setup.model_bases.base_object import _DeclaredClass


class EntityMeta(BaseMeta):
    _owner_class: type[Entity] | InheritValue = InheritValue.AS_DEFAULT
    abstract: Annotated[bool, MetaRules.DO_NOT_INHERIT] = False
    create_with_id: bool | InheritValue = InheritValue.AS_DEFAULT
    view_extra_fields: Annotated[list[str], MetaRules.ACCUMULATE] = Field(
        default_factory=list
    )
    reference_view_extra_fields: Annotated[list[str], MetaRules.ACCUMULATE] = Field(
        default_factory=list
    )
    field_definitions: ModelFields = Field(default_factory=ModelFields)

    @property
    def fields(self) -> dict[str, FieldDefinition]:
        if self.field_definitions:
            return self.field_definitions.fields
        raise Exception(f"{self.__class__.__name__}.field_definition missing")


class EntityReferenceSet(BaseModel):
    pass


class Entity(_DeclaredClass, WithMeta[EntityMeta]):
    _meta: ClassVar[EntityMeta] = EntityMeta(create_with_id=False)  # pyright: ignore[reportIncompatibleVariableOverride]
    _action_classes: ClassVar[list[str]] = [
        "Create",
        "View",
        "Update",
        "ReferenceView",
        "ReferenceSet",
        "ReferenceCreate",
    ]

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs) -> None:
        from pangloss.model_setup.model_manager import ModelManager

        cls._initialised = False

        ModelManager.register_entity(cls)

        cls._meta: EntityMeta = cls._meta.model_copy(  # pyright: ignore[reportIncompatibleVariableOverride]
            update={"field_definitions": ModelFields()}
        )
        cls._meta._owner_class = cls

        ModelManager.try_initialise_all_models()

    @classmethod
    def __pangloss_post_init__(cls):
        pass

    ReferenceSet: ClassVar[EntityReferenceSet]
