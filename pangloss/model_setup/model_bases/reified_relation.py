from pydantic import BaseModel

from pangloss.model_setup.model_bases.base_object import _BaseObject


class ReifiedRelationMeta(BaseModel):
    pass


class ReifiedRelation[Target](_BaseObject):
    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs) -> None:

        if cls is ReifiedRelation:
            return

        from pangloss.model_setup.model_manager import ModelManager

        ModelManager.register_reified_relation(cls)

    target: Target


class ReifiedRelationDocument[Target](_BaseObject):
    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs) -> None:

        if cls is ReifiedRelation:
            return

        from pangloss.model_setup.model_manager import ModelManager

        ModelManager.register_reified_relation_document(cls)

    target: Target
