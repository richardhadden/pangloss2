from dataclasses import dataclass, field
from typing import Annotated, ClassVar

from pydantic import ConfigDict

from pangloss.model_setup.model_bases.base_object import _BaseObject
from pangloss.model_setup.model_bases.meta import META_RULES, BaseMeta


@dataclass(frozen=True, kw_only=True)
class DocumentMeta(BaseMeta):
    abstract: Annotated[bool, META_RULES.DO_NOT_INHERIT] = False
    create_with_id: bool = False
    view_extra_fields: Annotated[list[str], META_RULES.ACCUMULATE] = field(
        default_factory=list
    )
    reference_view_extra_fields: Annotated[list[str], META_RULES.ACCUMULATE] = field(
        default_factory=list
    )


class DocumentCreateBase(_BaseObject):
    pass


class Document(_BaseObject):
    model_config = ConfigDict(validate_assignment=True)

    _meta: ClassVar[DocumentMeta]

    Create: ClassVar[DocumentCreateBase]

    label: str

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs) -> None:
        from pangloss.model_setup.model_manager import ModelManager

        ModelManager.register_document(cls)
