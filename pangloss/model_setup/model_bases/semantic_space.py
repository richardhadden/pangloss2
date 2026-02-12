from pangloss.model_setup.model_bases.base_object import _BaseObject
from pangloss.model_setup.model_bases.sub_document import SubDocument


class SemanticSpace[Contents: SubDocument](_BaseObject):
    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs) -> None:
        from pangloss.model_setup.model_manager import ModelManager

        ModelManager.register_semantic_space(cls)

    contents: Contents
