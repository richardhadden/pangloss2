from pydantic import BaseModel

from pangloss.model_setup.model_bases.base_object import _BaseObject


class ConjunctionMeta(BaseModel):
    pass


class Conjunction(_BaseObject):
    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs) -> None:
        from pangloss.model_setup.model_manager import ModelManager

        ModelManager.register_conjunction(cls)
