from pangloss.model_setup.model_bases.base_object import _DeclaredClass


class EdgeModel(_DeclaredClass):
    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs) -> None:
        from pangloss.model_setup.model_manager import ModelManager

        ModelManager.register_edge_model(cls)
