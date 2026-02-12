from pydantic import BaseModel


class EdgeModel(BaseModel):
    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs) -> None:
        from pangloss.model_setup.model_manager import ModelManager

        ModelManager.register_edge_model(cls)
