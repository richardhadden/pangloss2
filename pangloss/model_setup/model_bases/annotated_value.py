from pangloss.model_setup.model_bases.base_object import _BaseObject
from pangloss.model_setup.model_bases.base_types import BaseTypes


class AnnotatedValue[T: type[BaseTypes]](_BaseObject):
    """Allows additional literal fields to be bound to a value"""

    value: T

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs) -> None:
        from pangloss.model_setup.model_manager import ModelManager

        ModelManager.register_annotated_value(cls)
