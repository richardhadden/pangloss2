from typing import Any

from pydantic import BaseModel, create_model


class Reified[T](BaseModel):
    target: T

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs: Any) -> None:
        print("running")
        print(cls.__name__, cls.__pydantic_generic_metadata__)
        print(">", cls.model_fields["target"].annotation)
        cls.Create = create_model(f"{cls.__name__}Create", target=T)


class MyModel[T, U](Reified[T]):
    other: U


class Stuff(BaseModel):
    pass
