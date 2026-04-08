from typing import ClassVar, Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic_meta_kit import InheritValue

from pangloss.model_setup.field_definitions import (
    FieldDefinition,
    ModelFieldDict,
    ModelFields,
)
from pangloss.model_setup.model_bases.base_object import (
    _CreateBase,
    _CreateDBBase,
    _DeclaredClass,
)


class ReifiedRelationMeta(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    _owner_class: type[ReifiedRelation] | InheritValue = InheritValue.AS_DEFAULT
    require_label: Literal[False] = False

    field_definitions: ModelFields = Field(default_factory=ModelFields)

    @property
    def fields(self) -> ModelFieldDict[str, FieldDefinition]:
        return self.field_definitions.fields


class _ReifiedRelationCreateBase(_CreateBase):
    pass


class _ReifiedRelationCreateDBBase(_CreateDBBase):
    pass


class ReifiedRelation[TTarget](_DeclaredClass):
    Meta: ClassVar[type[ReifiedRelationMeta]] = ReifiedRelationMeta
    model_config = ConfigDict(validate_assignment=True)
    _meta: ClassVar[ReifiedRelationMeta] = ReifiedRelationMeta()  # pyright: ignore[reportIncompatibleVariableOverride]

    Create: ClassVar[type[_ReifiedRelationCreateBase]]
    CreateDB: ClassVar[type[_ReifiedRelationCreateDBBase]]

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


class _ReifiedRelationDocumentCreateBase(_CreateBase):
    pass


class _ReifiedRelationDocumentCreateDBBase(_CreateDBBase):
    pass


class ReifiedRelationDocument[Target](_DeclaredClass):
    Create: ClassVar[type[_ReifiedRelationDocumentCreateBase]]
    CreateDB: ClassVar[type[_ReifiedRelationCreateDBBase]]

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs) -> None:

        if cls is ReifiedRelation:
            return

        from pangloss.model_setup.model_manager import ModelManager

        ModelManager.register_reified_relation_document(cls)

        ModelManager.try_initialise_all_models(cls)

    target: Target
