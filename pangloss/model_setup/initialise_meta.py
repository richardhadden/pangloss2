from typing import cast

from pangloss.model_setup.model_bases.document import (
    DOCUMENT_META_DO_NOT_INHERIT_FIELDS,
    DocumentMeta,
)
from pangloss.models import ALL_MODELS, Document
from pangloss.types import ModelTypes


def get_parent_class[T: type[ModelTypes]](model: T) -> T:
    mro0 = model.mro()[0]
    mro1 = model.mro()[1]
    parent = mro1 if mro1 not in ALL_MODELS else mro0
    assert parent
    return cast(T, parent)


def initialise_document_meta(model: type[Document]):
    print("======", model.__name__)
    parent_class = get_parent_class(model)
    if model._class_has_own_meta() and parent_class._meta:
        new_dict = {}
        for k, v in DocumentMeta.__dataclass_fields__.items():
            if (
                getattr(parent_class._meta, k) != v.default
                and k not in DOCUMENT_META_DO_NOT_INHERIT_FIELDS
            ):
                print(k, getattr(parent_class._meta, k))
                new_dict[k] = getattr(parent_class._meta, k)

        print(new_dict)

    else:
        if parent_class._meta:
            model._meta = DocumentMeta(
                **{
                    k: v
                    for k, v in parent_class._meta.__class__.__dataclass_fields__.items()
                    if k not in DOCUMENT_META_DO_NOT_INHERIT_FIELDS
                }
            )

        else:
            model._meta = DocumentMeta()
