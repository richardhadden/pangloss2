import inspect
from collections.abc import Iterable
from enum import Enum
from functools import reduce
from typing import Any, ClassVar, cast

from pydantic import BaseModel, PrivateAttr, ValidationError
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefinedType

from pangloss.exceptions import PanglossMetaError


def get_field_rule(field: FieldInfo) -> META_RULES:
    if field.metadata:
        return field.metadata[0]
    else:
        return META_RULES.REPLACE_IF_NOT_DEFAULT


class InheritValueMetaclass(type):
    @property
    def AS_DEFAULT(cls):
        if not hasattr(cls, "_singleton_instance"):
            cls._singleton_instance = cls()
        return cls._singleton_instance


class INHERIT_VALUE(metaclass=InheritValueMetaclass):
    pass


def merge_fields[T: list | set | dict](field_type: type[T], left: T, right: T) -> T:
    if field_type is dict:
        return field_type(**left, **right)
    else:
        return field_type([*left, *right])


def generate_error_message(
    cls_name: str, do_not_inherits_invalid: list[str], accumulations_invalid: list[str]
) -> str:
    error_msg = f"Error with <{cls_name}>: "

    if do_not_inherits_invalid:
        error_msg += (
            f"field{'s' if len(do_not_inherits_invalid) > 1 else ''} {', '.join(f"'{f}'" for f in do_not_inherits_invalid)} "
            f"{'are' if len(do_not_inherits_invalid) > 1 else 'is'} annotated with "
            f"META_RULES.DO_NOT_INHERIT but do{'' if len(do_not_inherits_invalid) > 1 else 'es'} not provide a default value "
            "or default_factory"
        )
    if do_not_inherits_invalid and accumulations_invalid:
        error_msg += "; "
    if accumulations_invalid:
        error_msg += (
            f"field{'s' if len(accumulations_invalid) > 1 else ''} {', '.join(f"'{f}'" for f in accumulations_invalid)} "
            f"{'are' if len(accumulations_invalid) > 1 else 'is'} annotated with "
            f"META_RULES.ACCUMULATE but {'are' if len(accumulations_invalid) > 1 else 'is'} not of type Iterable"
        )
    return error_msg


class BaseMeta(BaseModel):
    model_config = {"arbitrary_types_allowed": True}

    _initialised_directly: set[str] = PrivateAttr(default_factory=set)

    @classmethod
    def __pydantic_init_subclass__(cls, **_):
        cls.run_initialisation_checks()

    @classmethod
    def run_initialisation_checks(cls):
        do_not_inherits_invalid: list[str] = []
        accumulations_invalid: list[str] = []
        for field_name, model_field in cls.model_fields.items():
            # Checks that all fields that are DO_NOT_INHERIT provide a default value
            if get_field_rule(model_field) == META_RULES.DO_NOT_INHERIT and (
                isinstance(model_field.default, PydanticUndefinedType)
                or isinstance(
                    model_field.get_default(call_default_factory=True),
                    PydanticUndefinedType,
                )
            ):
                do_not_inherits_invalid.append(field_name)

            # Checks that fields that are ACCUMULATE are of type Iterable
            if get_field_rule(model_field) == META_RULES.ACCUMULATE and (
                (
                    inspect.isclass(model_field.annotation)
                    and not issubclass(model_field.annotation, Iterable)
                )
                or not isinstance(
                    model_field.get_default(call_default_factory=True), Iterable
                )
            ):
                accumulations_invalid.append(field_name)

        if do_not_inherits_invalid or accumulations_invalid:
            raise PanglossMetaError(
                generate_error_message(
                    cls.__name__, do_not_inherits_invalid, accumulations_invalid
                )
            )

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self._initialised_directly.update(kwargs.keys())

    def __and__[T: BaseMeta](self: T, child: T | None) -> T:

        # If there is nothing to be added, return self

        # Check self and child have same time, for sanity
        if child and type(self) is not type(child):
            raise PanglossMetaError("Cannot merge two Meta objects of different types")

        left_dict: dict[str, Any] = self.model_dump()
        if child is None:
            right_dict = {}
        else:
            right_dict: dict[str, Any] = child.model_dump()

        merged_dict: dict[str, Any] = {}

        for field_name, model_field in self.__class__.model_fields.items():
            field_rule: META_RULES = get_field_rule(model_field)

            if field_rule == META_RULES.ACCUMULATE:
                merged_dict[field_name] = merge_fields(
                    field_type=type(model_field.get_default(call_default_factory=True)),
                    left=left_dict[field_name],
                    right=right_dict[field_name],
                )

            # A field defined explicitly on a meta object should be used
            elif child and field_name in child._initialised_directly:
                merged_dict[field_name] = right_dict[field_name]

            # A field not defined explicitly and that can inherit
            # should inherit
            elif (
                not child or field_name not in child._initialised_directly
            ) and field_rule != META_RULES.DO_NOT_INHERIT:
                merged_dict[field_name] = left_dict[field_name]

        return self.__class__(**merged_dict)


class META_RULES(Enum):
    DO_NOT_INHERIT = 0
    ACCUMULATE = 1
    REPLACE_IF_NOT_DEFAULT = 2


class WithMeta[T: BaseMeta](BaseModel):
    _meta: ClassVar[T]  # type: ignore
    _meta_class: ClassVar[type[T]]  # type: ignore

    @classmethod
    def __pydantic_init_subclass__(cls, **_) -> None:
        print("---", cls.__name__)

        initialising_class_is_this = (
            cls.__pydantic_generic_metadata__["origin"] is __class__
        )

        if initialising_class_is_this:
            __class__._meta_class = cls.__pydantic_generic_metadata__["args"][0]

        if initialising_class_is_this:
            return

        has_own_meta = "_meta" in cls.__dict__

        parent_classes: list[type] = []
        for c in cls.mro():
            if c is not cls:
                parent_classes.append(c)

        parents_metas = []
        for parent in parent_classes:
            if (parent_meta := getattr(parent, "_meta", None)) and isinstance(
                parent_meta, BaseMeta
            ):
                parents_metas.append(parent_meta)

        meta_class: type[BaseMeta] = cast(type[BaseMeta], cls._meta_class)

        if not has_own_meta and not parents_metas:
            try:
                cls._meta = meta_class()  # type: ignore

            except ValidationError:
                raise PanglossMetaError(
                    f"<{cls.__name__}>: a _meta field with instance of type {meta_class.__name__} must "
                    "be declared somewhere in the model hierarchy, or have all-default arguments"
                )

        elif not has_own_meta:
            cls._meta = reduce(lambda x, y: x & y, [*parents_metas, None])  # type: ignore

        elif has_own_meta:
            cls._meta = reduce(
                lambda x, y: x & y, [*parents_metas, cls.__dict__["_meta"]]
            )

        for k, v in cls._meta.model_dump().items():
            if isinstance(v, INHERIT_VALUE):
                raise PanglossMetaError(
                    f"<{cls.__name__}>: field '{k}' of _meta instance can inherit a value, "
                    "but this is never declared in the object hierarchy"
                )
