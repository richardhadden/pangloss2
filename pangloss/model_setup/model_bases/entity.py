from typing import Annotated, ClassVar, Self

from pydantic import ConfigDict, Field, model_validator
from pydantic_meta_kit import BaseMeta, InheritValue, MetaRules, WithMeta

from pangloss.exceptions import PanglossMetaError
from pangloss.model_setup.field_definitions import (
    FieldDefinition,
    ModelFieldDict,
    ModelFields,
)
from pangloss.model_setup.model_bases.base_object import (
    _CreateBase,
    _CreateDBBase,
    _DeclaredClass,
    _ReferenceSetBase,
    _ReferenceViewBase,
)


class EntityMeta(BaseMeta):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    _owner_class: type[Entity] | InheritValue = InheritValue.AS_DEFAULT
    abstract: Annotated[bool, MetaRules.DO_NOT_INHERIT] = False
    create_with_id: bool | InheritValue = False
    create_inline: bool | InheritValue = False
    accept_url_as_id: bool | InheritValue = True
    view_extra_fields: Annotated[list[str], MetaRules.ACCUMULATE] = Field(
        default_factory=list
    )
    reference_view_extra_fields: Annotated[list[str], MetaRules.ACCUMULATE] = Field(
        default_factory=list
    )
    field_definitions: ModelFields = Field(default_factory=ModelFields)

    @property
    def fields(self) -> ModelFieldDict[str, FieldDefinition]:
        if self.field_definitions:
            return self.field_definitions.fields
        raise Exception(f"{self.__class__.__name__}.field_definition missing")

    @model_validator(mode="after")
    def check_create_with_id_set_with_create_inline(self) -> Self:
        if self.create_inline and not self.create_with_id:
            raise PanglossMetaError(
                "If EntityMeta.create_inline=True, EntityMeta.create_with_id must also be set to True"
            )
        return self


class _EntityCreateBase(_CreateBase):
    pass


class _EntityCreateDBBase(_CreateDBBase):
    pass


class _EntityReferenceSetBase(_ReferenceSetBase):
    pass


class _EntityReferenceView(_ReferenceViewBase):
    pass


class Entity(_DeclaredClass, WithMeta[EntityMeta]):
    Meta: ClassVar[type[EntityMeta]] = EntityMeta
    _meta: ClassVar[EntityMeta] = EntityMeta(create_with_id=False)  # pyright: ignore[reportIncompatibleVariableOverride]

    Create: ClassVar[type[_EntityCreateBase]]
    CreateDB: ClassVar[type[_EntityCreateDBBase]]
    ReferenceSet: ClassVar[type[_EntityReferenceSetBase]]
    ReferenceView: ClassVar[type[_EntityReferenceView]]

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs) -> None:
        from pangloss.model_setup.model_manager import ModelManager

        cls._initialised = False

        ModelManager.register_entity(cls)

        cls._meta = cls.__dict__.get("_meta", EntityMeta(_owner_class=cls))  # pyright: ignore[reportIncompatibleVariableOverride]

        cls._meta._owner_class = cls

        ModelManager.try_initialise_all_models(cls)

    @classmethod
    def __pangloss_post_init__(cls):
        pass
