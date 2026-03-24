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
    abstract: Annotated[bool, MetaRules.DO_NOT_INHERIT] = False
    create_with_id: bool | InheritValue = InheritValue.AS_DEFAULT
    view_extra_fields: Annotated[list[str], MetaRules.ACCUMULATE] = Field(
        default_factory=list
    )
    reference_view_extra_fields: Annotated[list[str], MetaRules.ACCUMULATE] = Field(
        default_factory=list
    )
    field_definitions: ModelFields = Field(default_factory=ModelFields)
    _owner_class: type[Document] | InheritValue = InheritValue.AS_DEFAULT

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
    """An arbitrarily complex object, with nestable subdocuments and relations to Entities"""

    Meta: ClassVar[type[DocumentMeta]] = DocumentMeta
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

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs) -> None:

        from pangloss.model_setup.model_manager import ModelManager

        # Set model it uninitialised, as may inherit _initialised from parent class
        cls._initialised = False

        # Make sure _meta class is new and not inherited
        cls._meta = cls.__dict__.get("_meta", DocumentMeta())  # pyright: ignore[reportIncompatibleVariableOverride]

        # Set owner class on cls._meta
        cls._meta._owner_class = cls

        ModelManager.register_document(cls)
        ModelManager.try_initialise_all_models(cls)
