from datetime import date, datetime
from functools import cache
from inspect import isclass
from types import UnionType
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    Iterable,
    TypeIs,
    TypeVar,
    Union,
    cast,
    get_args,
    get_origin,
)

from annotated_types import BaseMetadata
from frozendict import frozendict
from pydantic._internal._generics import PydanticGenericMetadata
from pydantic.fields import FieldInfo

from pangloss.exceptions import PanglossModelError
from pangloss.model_setup.field_definitions import (
    EmbeddedFieldDefinition,
    EmbeddedOption,
    FieldDefinition,
    FieldFulfilment,
    FieldSubclassing,
    ListFieldDefinition,
    LiteralFieldDefinition,
    ParameterTypeOptions,
    RelationFieldDefinition,
    RelationOption,
    RelationToConjunction,
    RelationToDocument,
    RelationToEntity,
    RelationToReifiedRelation,
    RelationToSemanticSpace,
    RelationToTypeVar,
    TRelationFieldDefinitionAnnotation,
)
from pangloss.model_setup.model_bases.base_object import _DeclaredClass
from pangloss.model_setup.model_bases.configs import RelationConfig
from pangloss.model_setup.model_bases.conjunction import Conjunction
from pangloss.model_setup.model_bases.document import Document
from pangloss.model_setup.model_bases.edge_model import EdgeModel
from pangloss.model_setup.model_bases.embedded import Embedded
from pangloss.model_setup.model_bases.entity import Entity
from pangloss.model_setup.model_bases.helpers import Fulfils, ViaEdge
from pangloss.model_setup.model_bases.reified_relation import ReifiedRelation
from pangloss.model_setup.model_bases.semantic_space import SemanticSpace
from pangloss.model_setup.model_bases.trait import NonHeritableTrait
from pangloss.model_setup.utils import (
    get_all_parent_classes,
    get_concrete_types,
    get_direct_instantiations_of_trait,
    model_is_trait,
)

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


def is_embedded(annotation: type[Any] | UnionType | None) -> TypeIs[type[Embedded]]:
    if isclass(annotation) and issubclass(annotation, Embedded):
        return True
    return False


def is_union_of_embedded(
    annotation: type[Any] | None | UnionType,
) -> TypeIs[type[Embedded | Embedded]]:
    if isinstance(annotation, UnionType):
        if all(is_embedded(arg) for arg in get_args(annotation)):
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

    if isclass(annotation) and issubclass(annotation, (_DeclaredClass)):
        return True
    return False


def is_single_relatable(annotation: type[Any]) -> TypeIs[type[_DeclaredClass]]:
    if isclass(annotation) and issubclass(annotation, _DeclaredClass):
        return True
    return False


def is_list_relatable(annotation: type[Any] | None) -> bool:

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


def flatten[T](xss: Iterable[Iterable[T]]) -> list[T]:
    return [x for xs in xss for x in xs]


def build_relation_options(
    model: type[_DeclaredClass],
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
                build_relation_options(model, union_arg, edge_model=edge_model)
            )

    if (
        isclass(annotation)
        and issubclass(annotation, _DeclaredClass)
        and (origin := annotation.__pydantic_generic_metadata__["origin"])
        and isclass(origin)
        and issubclass(origin, (ReifiedRelation, SemanticSpace, Conjunction))
    ):
        type_args = annotation.__pydantic_generic_metadata__["args"]
        parameters = origin.__pydantic_generic_metadata__["parameters"]
        params_type_args = zip(parameters, type_args)
        for t in type_args:
            if (
                isclass(t)
                and issubclass(t, (_DeclaredClass))
                and not is_parameterized_generic(t)
            ):
                model.depends_on_classes.add(t)

        type_options = {
            type_var.__name__: ParameterTypeOptions[type[origin]](
                annotated_type=type_arg,
                type_var=type_var,
                type_var_name=type_var.__name__,
                type_options=frozenset(
                    build_relation_options(model, type_arg, edge_model=edge_model)
                ),
            )
            for type_var, type_arg in params_type_args
        }

        if issubclass(origin, ReifiedRelation):
            model.depends_on_classes.add(origin)
            relation_options.append(
                RelationToReifiedRelation(
                    annotated_type=annotation,
                    edge_model=edge_model,
                    reified_relation_type=origin,
                    parameter_type_options=frozendict(type_options),
                )
            )
        if issubclass(origin, SemanticSpace):
            model.depends_on_classes.add(origin)
            for concrete_semantic_space in get_concrete_types(origin):
                relation_options.append(
                    RelationToSemanticSpace(
                        annotated_type=annotation,
                        edge_model=edge_model,
                        semantic_space_type=concrete_semantic_space,
                        parameter_type_options=frozendict(type_options),
                    )
                )
        if issubclass(origin, Conjunction):
            model.depends_on_classes.add(origin)
            for concrete_conjunction in get_concrete_types(origin):
                relation_options.append(
                    RelationToConjunction(
                        annotated_type=annotation,
                        edge_model=edge_model,
                        conjunction_type=concrete_conjunction,
                        parameter_type_options=frozendict(type_options),
                    )
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

    if relation_config:
        field_subclassings = relation_config.subclasses_parent_fields
    else:
        field_subclassings = []

    reverse_name = (
        relation_config.reverse_name
        if relation_config and relation_config.reverse_name
        else f"{field_name}_reverse"
    )

    if (
        is_parameterized_generic(field_info.annotation)
        and isinstance((arg := get_args(field_info.annotation)[0]), TypeVar)
        and get_origin(field_info.annotation) is list
    ):
        return RelationFieldDefinition(
            field_name=field_name,
            field_on_model=model,
            annotated_type=field_info.annotation,  # pyright: ignore[reportArgumentType]
            type_options=set(
                [RelationToTypeVar(annotated_type=arg, type_var_name=arg.__name__)]
            ),
            subclasses_parent_fields=field_subclassings,
            reverse_name=reverse_name,
            wrapper=list,
        )
    elif isinstance(field_info.annotation, TypeVar):
        return RelationFieldDefinition(
            field_name=field_name,
            field_on_model=model,
            annotated_type=field_info.annotation,  # pyright: ignore[reportArgumentType]
            type_options=set(
                [
                    RelationToTypeVar(
                        annotated_type=field_info.annotation,
                        type_var_name=field_info.annotation.__name__,
                    )
                ]
            ),
            subclasses_parent_fields=field_subclassings,
            reverse_name=reverse_name,
            wrapper=None,
        )

    elif is_list_relatable(field_info.annotation):
        if TYPE_CHECKING:
            assert field_info.annotation

        # If wrapped in a list, unwrap the list type
        annotation = get_args(field_info.annotation)[0]

        if is_parameterized_generic(annotation) and isclass(
            (origin := get_origin(annotation))
        ):
            model.depends_on_classes.add(origin)
        elif isclass(annotation):
            model.depends_on_classes.add(annotation)

        return RelationFieldDefinition(
            field_name=field_name,
            field_on_model=model,
            annotated_type=field_info.annotation,
            type_options=build_relation_options(model, annotation),
            subclasses_parent_fields=field_subclassings,
            reverse_name=reverse_name,
            wrapper=list,
        )

    else:
        if TYPE_CHECKING:
            assert is_relatable(field_info.annotation)
            assert is_single_relatable(field_info.annotation)

        if is_parameterized_generic(field_info.annotation) and isclass(
            (origin := get_origin(field_info.annotation))
        ):
            model.depends_on_classes.add(origin)  # pyright: ignore[reportArgumentType]
            model.depends_on_classes.update(get_args(field_info.annotation))
        else:
            model.depends_on_classes.add(field_info.annotation)

        return RelationFieldDefinition(
            field_name=field_name,
            field_on_model=model,
            annotated_type=field_info.annotation,
            type_options=build_relation_options(model, field_info.annotation),
            subclasses_parent_fields=field_subclassings,
            reverse_name=reverse_name,
            wrapper=None,
        )


def build_embedded_field_definition(
    field_name: str, field_info: FieldInfo, model: type[_DeclaredClass]
) -> EmbeddedFieldDefinition:
    if TYPE_CHECKING:
        assert is_embedded(field_info.annotation) or is_union_of_embedded(
            field_info.annotation
        )

    field_options: set[type[Embedded]] = get_concrete_types(field_info.annotation)

    if isclass(field_info.annotation):
        model.depends_on_classes.add(field_info.annotation)

    return EmbeddedFieldDefinition(
        field_name=field_name,
        field_on_model=model,
        annotated_type=cast(
            type[Embedded] | type[Embedded | Embedded], field_info.annotation
        ),
        type_options=set(
            EmbeddedOption(annotated_type=option) for option in field_options
        ),
    )


@cache
def get_relation_config(field_info: FieldInfo) -> RelationConfig | None:
    if field_info.metadata and (
        rcs := [md for md in field_info.metadata if isinstance(md, RelationConfig)]
    ):
        relation_config = cast(RelationConfig, rcs[0])
        return relation_config
    return None


def get_field_origin_model_and_definition(
    model: type[_DeclaredClass], field_name: str
) -> tuple[type[_DeclaredClass], FieldDefinition] | tuple[None, None]:

    last_parent_with_field: type[_DeclaredClass] | None = None

    for parent_class in get_all_parent_classes(model):
        if parent_class.__pydantic_generic_metadata__["origin"] is Fulfils:
            fulfiled_class = parent_class.__pydantic_generic_metadata__["args"][0]
            if (
                issubclass(fulfiled_class, _DeclaredClass)
                and field_name in fulfiled_class.model_fields
            ):
                last_parent_with_field = fulfiled_class
        elif field_name in parent_class.model_fields:
            last_parent_with_field = parent_class

        else:
            continue

    if last_parent_with_field:
        return last_parent_with_field, last_parent_with_field._meta.fields[field_name]

    return None, None


def normalise_and_get_subclassed_fields(
    model: type[_DeclaredClass],
) -> dict[str, FieldSubclassing]:
    subclassed_fields = {}
    for field_name, field_info in model.model_fields.items():
        if relation_config := get_relation_config(field_info):
            field_subclassings = []
            for field_subclassing in relation_config.subclasses_parent_fields:
                if isinstance(field_subclassing, FieldSubclassing):
                    if (
                        field_subclassing.field_name
                        not in field_subclassing.field_on_model.model_fields
                    ):
                        raise PanglossModelError(
                            f"{model.__name__}.{field_name} is trying to subclass a field ('{field_subclassing}') that does not exist on a parent class"
                        )

                    subclassed_fields[field_subclassing.field_name] = FieldSubclassing(
                        field_name=field_subclassing.field_name,
                        disambiguator=field_subclassing.disambiguator,
                        field_on_model=field_subclassing.field_on_model,
                        subclassed_field_definition=field_subclassing.field_on_model._meta.fields[
                            field_subclassing.field_name
                        ],
                    )
                    field_subclassings.append(
                        subclassed_fields[field_subclassing.field_name]
                    )
                else:
                    assert isinstance(field_subclassing, str)
                    origin_class, definition = get_field_origin_model_and_definition(
                        model, field_subclassing
                    )

                    if not origin_class:
                        raise PanglossModelError(
                            f"{model.__name__}.{field_name} is trying to subclass a field ('{field_subclassing}') that does not exist on a parent class"
                        )

                    subclassed_fields[field_subclassing] = FieldSubclassing(
                        field_subclassing,
                        disambiguator=None,
                        field_on_model=origin_class,
                        subclassed_field_definition=definition,
                    )
                    field_subclassings.append(subclassed_fields[field_subclassing])

            relation_config.subclasses_parent_fields = field_subclassings
    return subclassed_fields


def field_is_from_indirect_non_heritable_model(model: type[_DeclaredClass], field_name):
    parent_classes = get_all_parent_classes(model)
    indirect_non_heritable_classes: list[type[NonHeritableTrait]] = [
        pc
        for pc in parent_classes
        if model_is_trait(pc)
        and issubclass(pc, NonHeritableTrait)
        and model not in get_direct_instantiations_of_trait(pc)
    ]
    for indirect_nht in indirect_non_heritable_classes:
        if field_name in indirect_nht._meta.fields:
            return True
    return False


def get_fields_on_model(model: type[_DeclaredClass]):
    """Yields an iterable of field name and field info for a model, removing subclassed
    fields"""

    subclassed_fields = normalise_and_get_subclassed_fields(model)

    for field_name, field_info in model.model_fields.items():
        if (
            field_name in subclassed_fields
            or field_is_from_indirect_non_heritable_model(model, field_name)
        ):
            continue

        yield field_name, field_info, None

    fulfilments = [
        f
        for f in get_all_parent_classes(model)
        if issubclass(f, Fulfils) and f.__pydantic_generic_metadata__["args"]
    ]
    for f in fulfilments:
        fulfilled_type: type[_DeclaredClass] = f.__pydantic_generic_metadata__["args"][
            0
        ]
        for field_name, field_info in fulfilled_type.model_fields.items():
            if field_name in subclassed_fields:
                continue

            yield (
                field_name,
                field_info,
                FieldFulfilment(field_name=field_name, fulfils_class=fulfilled_type),
            )


def check_subclass_type(field_definition: RelationFieldDefinition):
    """Given a completed field definition, checks that the"""
    for spf in field_definition.subclasses_parent_fields:
        assert isinstance(spf, FieldSubclassing)
        assert isinstance(spf.subclassed_field_definition, RelationFieldDefinition)

        field_type_options = set(
            flatten(
                get_concrete_types(f.annotated_type)
                for f in field_definition.type_options
            )
        )
        subclassed_field_type_options = set(
            flatten(
                get_concrete_types(f.annotated_type)
                for f in spf.subclassed_field_definition.type_options
            )
        )

        if not field_type_options.issubset(subclassed_field_type_options):
            raise PanglossModelError(
                f"{field_definition.field_on_model.__name__}.{field_definition.field_name} subclasses {spf.field_on_model}.{spf.field_name} "
                "but is not of the same type or narrowing of type"
            )


def initialise_field_definitions(model: type[_DeclaredClass]):

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

    for field_name, field_info, field_fulfilment in get_fields_on_model(model):
        print(
            ">>",
            model.__name__,
            field_name,
            model_required_to_fulfil,
            model_field_required_to_fulfil,
        )

        if field_name == "type":
            continue

        if (
            issubclass(model, SemanticSpace)
            and model is not SemanticSpace
            and model.__pydantic_generic_metadata__["origin"] is None
        ):
            model._meta.field_definitions.add_field(
                name=field_name,
                field_definition=build_relatable_field_definition(
                    field_name, field_info, model
                ),
            )

        if (
            issubclass(model, Conjunction)
            and model is not Conjunction
            and model.__pydantic_generic_metadata__["origin"] is None
        ):
            model._meta.field_definitions.add_field(
                name=field_name,
                field_definition=build_relatable_field_definition(
                    field_name, field_info, model
                ),
            )

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

        if is_embedded(field_info.annotation) or is_union_of_embedded(
            field_info.annotation
        ):
            model._meta.field_definitions.add_field(
                name=field_name,
                field_definition=build_embedded_field_definition(
                    field_name, field_info, model
                ),
            )

        elif is_relatable(field_info.annotation) or is_list_relatable(
            field_info.annotation
        ):
            field_definition = build_relatable_field_definition(
                field_name, field_info, model
            )
            if model_field_required_to_fulfil and model_required_to_fulfil:
                field_definition.field_required_to_fulfil.append(
                    FieldFulfilment(
                        field_name=model_field_required_to_fulfil,
                        fulfils_class=model_required_to_fulfil,
                    )
                )

            check_subclass_type(field_definition)

            model._meta.field_definitions.add_field(
                name=field_name,
                field_definition=field_definition,
            )

        elif is_list_of_literal(field_info.annotation):
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
