from datetime import date, datetime
from inspect import isclass
from types import UnionType
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    TypeIs,
    TypeVar,
    Union,
    cast,
    get_args,
    get_origin,
)

from annotated_types import BaseMetadata
from pydantic._internal._generics import PydanticGenericMetadata
from pydantic.fields import FieldInfo

from pangloss.exceptions import PanglossModelError
from pangloss.model_setup.field_definitions import (
    ListFieldDefinition,
    LiteralFieldDefinition,
    RelationFieldDefinition,
    RelationOption,
    RelationToDocument,
    RelationToEntity,
    RelationToTypeVar,
    TRelationFieldDefinitionAnnotation,
)
from pangloss.model_setup.model_bases.configs import RelationConfig
from pangloss.model_setup.model_bases.document import Document
from pangloss.model_setup.model_bases.edge_model import EdgeModel
from pangloss.model_setup.model_bases.entity import Entity
from pangloss.model_setup.model_bases.helpers import ViaEdge
from pangloss.model_setup.model_bases.reified_relation import ReifiedRelation
from pangloss.model_setup.model_bases.trait import HeritableTrait, NonHeritableTrait
from pangloss.model_setup.utils import get_concrete_types

if TYPE_CHECKING:
    from pangloss.model_setup.model_bases.base_object import _DeclaredClass


LITERAL_TYPES = {str, int, float, date, datetime}

type LiteralTypes = str | int | float | date | datetime


def is_literal(
    annotation: type[Any] | None,
) -> TypeIs[type[str | int | float | date | datetime]]:
    """Checks whether an annotation is of a literal type"""
    return annotation in LITERAL_TYPES


def is_list_of_literal(
    annotation: type[Any] | None,
) -> TypeIs[type[list[str | int | float | date | datetime]]]:

    # list[X]
    if get_origin(annotation) is not list:
        return False
    # (X,)
    args = get_args(annotation)
    if not args:
        return False

    inner_type = args[0]

    if is_literal(inner_type):
        return True

    if get_origin(inner_type) is Annotated:
        inner_type_args = get_args(inner_type)
        if not inner_type_args:
            return False
        if is_literal(inner_type_args[0]):
            return True
    return False


def is_union_of_relatable(
    annotation: type[Any] | None | UnionType,
) -> TypeIs[UnionType]:
    if isinstance(annotation, UnionType):
        return all(is_relatable(arg) for arg in get_args(annotation))
    return False


def is_via_edge(
    annotation: type[Any] | None | UnionType,
) -> TypeIs[type[ViaEdge[Document | Entity, EdgeModel]]]:
    generic_metadata: PydanticGenericMetadata | None = getattr(
        annotation, "__pydantic_generic_metadata__", None
    )
    if generic_metadata and generic_metadata["origin"] is ViaEdge:
        if is_relatable(generic_metadata["args"][0]):
            return True
    return False


def get_model_and_edge_type(
    annotation: type[ViaEdge[type[Document | Entity], EdgeModel]],
) -> tuple[type[Document | Entity], type[EdgeModel]]:
    generic_metadata: PydanticGenericMetadata | None = getattr(
        annotation, "__pydantic_generic_metadata__", None
    )
    if generic_metadata and generic_metadata["origin"] is ViaEdge:
        if is_relatable(generic_metadata["args"][0]) and issubclass(
            generic_metadata["args"][1], EdgeModel
        ):
            return cast(
                tuple[type[Document | Entity], type[EdgeModel]],
                generic_metadata["args"],
            )

    raise PanglossModelError("ViaEdge model incorrectly used")


def is_relatable(
    annotation: type[Any] | None | type[Any | Any] | UnionType,
) -> TypeIs[type[_DeclaredClass] | type[Union[_DeclaredClass, _DeclaredClass]]]:
    # from pangloss.model_setup.model_bases.document import Document
    # from pangloss.model_setup.model_bases.entity import Entity

    if is_union_of_relatable(annotation):
        return True

    if is_via_edge(annotation):
        return True

    if isclass(annotation) and issubclass(
        annotation, (Document, Entity, HeritableTrait, NonHeritableTrait)
    ):
        return True
    return False


def is_single_relatable(annotation: type[Any]) -> TypeIs[type[_DeclaredClass]]:
    if isclass(annotation) and issubclass(annotation, _DeclaredClass):
        return True
    return False


def is_list_relatable(annotation: type[Any] | None):

    # list[X]
    if get_origin(annotation) is not list:
        return False
    # (X,)
    args = get_args(annotation)
    if not args:
        return False

    inner_type = args[0]

    if is_relatable(inner_type):
        return True

    if get_origin(inner_type) is Annotated:
        inner_type_args = get_args(inner_type)
        if not inner_type_args:
            return False
        if is_relatable(inner_type_args[0]):
            return True
    return False


def build_list_field_definition(
    field_name: str, field_info: FieldInfo, model: type[_DeclaredClass]
) -> ListFieldDefinition:
    try:
        assert field_info.annotation
        list_inner_type_tuple: tuple[Any, ...] = get_args(field_info.annotation)
        assert list_inner_type_tuple
        list_inner_type: Any = list_inner_type_tuple[0]

        inner_type_validators: list[BaseMetadata] = []
        if get_origin(list_inner_type) is Annotated:
            annotated_inner_type_tuple: tuple[Any, ...] = get_args(list_inner_type)
            assert annotated_inner_type_tuple
            list_inner_type = annotated_inner_type_tuple[0]
            inner_type_validators: list[BaseMetadata] = [
                arg
                for arg in annotated_inner_type_tuple
                if isinstance(arg, BaseMetadata)
            ]
        assert is_literal(list_inner_type)
        return ListFieldDefinition(
            field_on_model=model,
            field_name=field_name,
            annotated_type=field_info.annotation,
            validators=field_info.metadata,
            inner_type=list_inner_type,
            inner_type_validators=inner_type_validators,
        )
    except AssertionError:
        raise PanglossModelError(
            f"{model.__name__}.{field_name} has an invalid list field definition"
        )


def build_relation_options(
    annotation: TRelationFieldDefinitionAnnotation,
    edge_model: type[EdgeModel] | None = None,
) -> set[RelationOption]:
    relation_options = []

    if is_via_edge(annotation):
        annotation, edge_model = get_model_and_edge_type(annotation)  # pyright: ignore[reportArgumentType]
    else:
        annotation = annotation
        edge_model = edge_model

    origin = get_origin(annotation)

    if isclass(origin) and issubclass(origin, UnionType):
        for union_arg in get_args(annotation):
            relation_options.extend(
                build_relation_options(union_arg, edge_model=edge_model)
            )

    if isclass(annotation) and issubclass(annotation, Document):
        for concrete_type in get_concrete_types(annotation):
            relation_options.append(
                RelationToDocument(
                    annotated_type=concrete_type,
                    edge_model=edge_model,
                )
            )

    if isclass(annotation) and issubclass(annotation, Entity):
        for concrete_type in get_concrete_types(annotation):
            relation_options.append(
                RelationToEntity(
                    annotated_type=concrete_type,
                    edge_model=edge_model,
                )
            )

    return set(relation_options)


def extract_relation_config(field_info: FieldInfo) -> RelationConfig | None:
    if not field_info.metadata:
        return None
    for metadata_object in field_info.metadata:
        if isinstance(metadata_object, RelationConfig):
            return metadata_object


def is_parameterized_generic(tp):
    return get_origin(tp) is not None and len(get_args(tp)) > 0


def build_relatable_field_definition(
    field_name: str, field_info: FieldInfo, model: type[_DeclaredClass]
) -> RelationFieldDefinition:

    relation_config = extract_relation_config(field_info)

    reverse_name = (
        relation_config.reverse_name
        if relation_config and relation_config.reverse_name
        else f"{field_name}_reverse"
    )

    if is_parameterized_generic(field_info.annotation) and isinstance(
        (arg := get_args(field_info.annotation)[0]), TypeVar
    ):
        return RelationFieldDefinition(
            field_name=field_name,
            field_on_model=model,
            annotated_type=field_info.annotation,  # pyright: ignore[reportArgumentType]
            type_options=set(
                [RelationToTypeVar(annotated_type=arg, type_var_name=arg.__name__)]
            ),
            overrides_parent_fields=[],
            reverse_name=reverse_name,
            wrapper=list,
        )

    if is_list_relatable(field_info.annotation):
        if TYPE_CHECKING:
            assert field_info.annotation

        # If wrapped in a list, unwrap the list type
        annotation = get_args(field_info.annotation)[0]

        if is_parameterized_generic(annotation):
            model.depends_on_classes.add(get_origin(annotation))
        else:
            model.depends_on_classes.add(annotation)

        return RelationFieldDefinition(
            field_name=field_name,
            field_on_model=model,
            annotated_type=field_info.annotation,
            type_options=build_relation_options(annotation),
            overrides_parent_fields=[],
            reverse_name=reverse_name,
            wrapper=list,
        )

    else:
        if TYPE_CHECKING:
            assert is_relatable(field_info.annotation)
            assert is_single_relatable(field_info.annotation)

        if is_parameterized_generic(field_info.annotation):
            model.depends_on_classes.add(get_origin(field_info.annotation))  # pyright: ignore[reportArgumentType]  # ty:ignore[invalid-argument-type]
            model.depends_on_classes.update(get_args(field_info.annotation))
        else:
            model.depends_on_classes.add(field_info.annotation)

        return RelationFieldDefinition(
            field_name=field_name,
            field_on_model=model,
            annotated_type=field_info.annotation,
            type_options=build_relation_options(field_info.annotation),
            overrides_parent_fields=[],
            reverse_name=reverse_name,
            wrapper=None,
        )


def initialise_field_definitions(model: type[_DeclaredClass]):
    from pangloss.model_setup.model_bases.edge_model import EdgeModel

    # TODO: REMOVE THIS HOOK WHEN ALL MODELS HAVE A META CLASS!!
    if not hasattr(model, "_meta"):
        return

    if issubclass(model, EdgeModel):
        for field_name, field_info in model.model_fields.items():
            if is_relatable(field_info.annotation) or is_list_relatable(
                field_info.annotation
            ):
                raise PanglossModelError(
                    f"EdgeModel {model.__name__} does not support relations ({model.__name__}.{field_name})"
                )

    for field_name, field_info in model.model_fields.items():
        if issubclass(model, ReifiedRelation):
            if get_origin(field_info.annotation) and isinstance(
                get_args(field_info.annotation)[0], TypeVar
            ):
                model._meta.field_definitions.add_field(
                    name=field_name,
                    field_definition=build_relatable_field_definition(
                        field_name, field_info, model
                    ),
                )

        if is_relatable(field_info.annotation) or is_list_relatable(
            field_info.annotation
        ):
            model._meta.field_definitions.add_field(
                name=field_name,
                field_definition=build_relatable_field_definition(
                    field_name, field_info, model
                ),
            )

        if is_list_of_literal(field_info.annotation):
            model._meta.field_definitions.add_field(
                name=field_name,
                field_definition=build_list_field_definition(
                    field_name, field_info, model
                ),
            )

        elif is_literal(field_info.annotation):
            model._meta.field_definitions.add_field(
                field_name,
                LiteralFieldDefinition(
                    field_on_model=model,
                    field_name=field_name,
                    annotated_type=field_info.annotation,
                    validators=[
                        md for md in field_info.metadata if isinstance(md, BaseMetadata)
                    ],
                ),
            )
