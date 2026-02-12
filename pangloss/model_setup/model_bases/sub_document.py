from typing import ClassVar

from pydantic import BaseModel

from pangloss.model_setup.model_bases.base_object import _BaseObject


class SubDocumentMeta(BaseModel):
    pass


class SubDocumentCreateBase(_BaseObject):
    pass


class SubDocument(_BaseObject):
    Create: ClassVar[SubDocumentCreateBase]

    def generate_label(self):
        pass

    @classmethod
    def __pydantic_init_subclass__(cls, **_) -> None:
        from pangloss.model_setup.model_manager import ModelManager

        ModelManager.register_subdocument(cls)
