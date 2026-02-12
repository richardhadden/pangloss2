from pydantic import BaseModel

from pangloss.model_setup.model_bases.base_object import _BaseObject


class TraitMeta(BaseModel):
    pass


class _Trait(_BaseObject):
    pass


class HeritableTrait(_Trait):
    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs) -> None:
        from pangloss.model_setup.model_manager import ModelManager

        ModelManager.register_heritable_trait(cls)


class NonHeritableTrait(_Trait):
    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs) -> None:
        from pangloss.model_setup.model_manager import ModelManager

        ModelManager.register_non_heritable_trait(cls)
