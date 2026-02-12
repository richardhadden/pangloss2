from typing import ClassVar

from pydantic import BaseModel

from pangloss.model_setup.model_bases.base_object import _BaseObject


class EntityReferenceSet(BaseModel):
    pass


class Entity(_BaseObject):
    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs) -> None:
        from pangloss.model_setup.model_manager import ModelManager

        ModelManager.register_entity(cls)

    label: str

    ReferenceSet: ClassVar[EntityReferenceSet]
