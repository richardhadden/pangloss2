from pangloss.model_setup.model_bases.base_object import _DeclaredClass
from pangloss.model_setup.model_bases.document import Document


class SemanticSpace[Contents: Document](_DeclaredClass):
    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs) -> None:
        from pangloss.model_setup.model_manager import ModelManager

        ModelManager.register_semantic_space(cls)

    contents: Contents
