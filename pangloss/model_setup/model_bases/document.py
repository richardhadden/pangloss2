from typing import Annotated, ClassVar

from pydantic import ConfigDict, Field
from pydantic_meta_kit import BaseMeta, MetaRules, WithMeta

from pangloss.model_setup.model_bases.base_object import _BaseObject


class DocumentMeta(BaseMeta):
    abstract: Annotated[bool, MetaRules.DO_NOT_INHERIT] = False
    create_with_id: bool = False
    view_extra_fields: Annotated[list[str], MetaRules.ACCUMULATE] = Field(
        default_factory=list
    )
    reference_view_extra_fields: Annotated[list[str], MetaRules.ACCUMULATE] = Field(
        default_factory=list
    )


class DocumentCreateBase(_BaseObject):
    pass


class Document(_BaseObject, WithMeta[DocumentMeta]):
    model_config = ConfigDict(validate_assignment=True)

    _meta: ClassVar[DocumentMeta]

    Create: ClassVar[DocumentCreateBase]

    label: str

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs) -> None:
        from pangloss.model_setup.model_manager import ModelManager

        ModelManager.register_document(cls)
