from typing import Annotated, ClassVar

from pydantic import ConfigDict, Field
from pydantic_meta_kit import BaseMeta, InheritValue, MetaRules, WithMeta

from pangloss.model_setup.field_definitions import FieldDefinition, ModelFields
from pangloss.model_setup.model_bases.base_object import (
    DeclaredClassMeta,
    _CreateBase,
    _DeclaredClass,
    _ReferenceSetBase,
    _ReferenceViewBase,
    _UpdateBase,
    _ViewBase,
)


class DocumentMeta(BaseMeta, DeclaredClassMeta):
    _owner_class: type[Document] | InheritValue = InheritValue.AS_DEFAULT
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
        return self.field_definitions.fields


class DocumentCreateBase[T](_CreateBase[T]):
    label: str


class DocumentViewBase[T](_ViewBase[T]):
    pass  # in_semantic_space: list[str] = Field(default_factory=list)


class DocumentUpdateBase[T: Document](_UpdateBase[T]):
    pass


class DocumentReferenceViewBase[T](_ReferenceViewBase[T]):
    pass


class DocumentReferenceSetBase[T](_ReferenceSetBase[T]):
    pass


class Document(_DeclaredClass, WithMeta[DocumentMeta]):
    model_config = ConfigDict(validate_assignment=True)

    _meta: ClassVar[DocumentMeta] = DocumentMeta(create_with_id=False)  # pyright: ignore[reportIncompatibleVariableOverride]
    _action_classes: ClassVar[list[str]] = [
        "Create",
        "View",
        "Update",
        "ReferenceView",
        "ReferenceSetBase",
    ]

    Create: ClassVar[type[DocumentCreateBase]]
    View: ClassVar[type[DocumentViewBase]]
    Update: ClassVar[type[DocumentUpdateBase]]

    ReferenceView: ClassVar[type[DocumentReferenceViewBase]]
    ReferenceSetBase: ClassVar[type[DocumentReferenceSetBase]]
    label: str

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs) -> None:

        from pangloss.model_setup.model_manager import ModelManager

        ModelManager.register_document(cls)
        ModelManager.try_initialise_all_models()

    @classmethod
    def __pangloss_post_init__(cls):
        cls._meta: DocumentMeta = cls._meta.model_copy(update={"_owner_class": cls})  # pyright: ignore[reportIncompatibleVariableOverride]
