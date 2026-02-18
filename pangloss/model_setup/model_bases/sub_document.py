from typing import Annotated, ClassVar

from pydantic import ConfigDict, Field
from pydantic_meta_kit import BaseMeta, InheritValue, MetaRules

from pangloss.model_setup.field_definitions import ModelFields
from pangloss.model_setup.model_bases.base_object import _DeclaredClass


class SubDocumentMeta(BaseMeta):
    _owner_class: type[SubDocument] | InheritValue = InheritValue.AS_DEFAULT
    abstract: Annotated[bool, MetaRules.DO_NOT_INHERIT] = False
    create_with_id: bool | InheritValue = InheritValue.AS_DEFAULT
    view_extra_fields: Annotated[list[str], MetaRules.ACCUMULATE] = Field(  # noqa: F821
        default_factory=list
    )
    reference_view_extra_fields: Annotated[list[str], MetaRules.ACCUMULATE] = Field(
        default_factory=list
    )
    model_field_container: ModelFields = Field(default_factory=ModelFields)

    @property
    def fields(self):
        return self.model_field_container.fields


class SubDocumentCreateBase(_DeclaredClass):
    pass


class SubDocument(_DeclaredClass):
    model_config = ConfigDict(validate_assignment=True)

    _meta: ClassVar[SubDocumentMeta] = SubDocumentMeta(create_with_id=False)

    Create: ClassVar[SubDocumentCreateBase]

    def generate_label(self):
        pass

    @classmethod
    def __pydantic_init_subclass__(cls, **_) -> None:
        from pangloss.model_setup.model_manager import ModelManager

        ModelManager.register_subdocument(cls)
        cls._meta._owner_class = cls
        ModelManager.try_initialise_all_models()
