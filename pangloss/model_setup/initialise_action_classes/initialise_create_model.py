import warnings
from typing import Literal, get_args, get_type_hints
from uuid import UUID

from pydantic import AnyHttpUrl
from pydantic import create_model as pydantic_create_model
from pydantic.fields import FieldInfo

from pangloss.model_setup.model_bases.base_object import _DeclaredClass


def build_id_field_on_create_model(model) -> None:
    assert model.Create
    if getattr(model._meta, "create_with_id", False):
        annotation = UUID | None
        if getattr(model._meta, "accept_url_as_id", False):
            annotation = UUID | AnyHttpUrl | None
        model.Create.model_fields["id"] = FieldInfo(annotation=annotation, default=None)
        model.Create.model_fields["create_new"] = FieldInfo(annotation=Literal[True])  # pyright: ignore[reportArgumentType]


def build_label_field_on_create_model(model):
    assert model.Create

    if getattr(model._meta, "require_label", True):
        model.Create.model_fields["label"] = FieldInfo(annotation=str)


def initialise_create_model(model: type[_DeclaredClass]):
    try:
        type_hints = get_type_hints(model)
    except:
        return

    if "Create" not in type_hints:
        warnings.warn(f"Create class hint missing from {model.__name__}")
        return

    # Extracts from the _DeclaredClass definition the annotation for .Create
    create_base_type = get_args(get_args(type_hints["Create"])[0])[0]

    model.Create = pydantic_create_model(
        f"{model.__name__}Create", __base__=create_base_type
    )  # pyright: ignore[reportAttributeAccessIssue]

    build_id_field_on_create_model(model)
    build_label_field_on_create_model(model)

    model.Create.model_rebuild(force=True)
