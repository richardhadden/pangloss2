import warnings
from typing import ClassVar, Literal, get_args, get_type_hints
from uuid import UUID

from pydantic import AnyHttpUrl, ConfigDict
from pydantic import create_model as pydantic_create_model
from pydantic.alias_generators import to_camel

from pangloss.model_setup.model_bases.base_object import _DeclaredClass
from pangloss.model_setup.model_bases.entity import Entity


def initialise_reference_model(model: type[_DeclaredClass]):
    if not issubclass(model, (Entity,)):
        return

    # Checks if Create model has already been created; do not duplicate as we depend
    # on model reference!
    if "ReferenceSet" in model.__dict__:
        return

    try:  # TODO! Remove this guard once all tests passing
        type_hints = get_type_hints(model)
    except Exception:
        return

    if "ReferenceSet" not in type_hints:
        warnings.warn(f"ReferenceSet class hint missing from {model.__name__}")
        return

    # Extracts from the _DeclaredClass definition the annotation for .Create
    reference_set_base_type = get_args(get_args(type_hints["ReferenceSet"])[0])[0]

    if model._meta.accept_url_as_id:
        id_type = UUID | AnyHttpUrl
    else:
        id_type = UUID

    model.ReferenceSet = pydantic_create_model(
        f"{model.__name__}ReferenceSet",
        __base__=reference_set_base_type,
        _owner=(ClassVar[model], model),
        __config__=ConfigDict(alias_generator=to_camel),
        type=(Literal[model.__name__], model.__name__),  # type: ignore
        id=id_type,
        label=(str | None, None),
    )  # pyright: ignore[reportAttributeAccessIssue]

    model.ReferenceSet.model_rebuild(force=True)
