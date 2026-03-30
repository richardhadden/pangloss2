from typing import Any

from pydantic import BaseModel, create_model


class Reified[T](BaseModel):
    target: T

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs: Any) -> None:
        print("running")
        print(cls.__name__, cls.__pydantic_generic_metadata__)
        for f, fi in cls.model_fields.items():
            print(">", fi.annotation)
        # print(">", cls.model_fields["target"].annotation)
        cls.Create = create_model(
            f"{cls.__name__}Create",
            __base__=cls,
            **{f: fi.annotation for f, fi in cls.model_fields.items()},
        )


class MyModel[T, U](Reified[T]):
    other: U


class Stuff(BaseModel):
    pass


print(MyModel.Create.__pydantic_generic_metadata__)
