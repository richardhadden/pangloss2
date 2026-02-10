from typing import ClassVar

from pydantic import BaseModel, ConfigDict


class DocumentMeta(BaseModel):
    __abstract__: bool = False


class SubDocumentMeta(BaseModel):
    pass


class ReifiedRelationMeta(BaseModel):
    pass


class TraitMeta(BaseModel):
    pass


class ConjunctionMeta(BaseModel):
    pass


class RelationConfig(BaseModel):
    reverse_name: str


class DocumentFieldConfig(RelationConfig):
    pass


class _BaseObject(BaseModel):
    pass


class EntityReferenceSet(BaseModel):
    pass


class Entity(_BaseObject):
    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs) -> None:
        from pangloss.model_setup.model_manager import ModelManager

        ModelManager.register_entity(cls)

    label: str

    ReferenceSet: ClassVar[EntityReferenceSet]


class CreateBase(_BaseObject):
    pass


class DocumentCreateBase(_BaseObject):
    Meta: ClassVar[DocumentMeta] = DocumentMeta()


class Document(_BaseObject):
    model_config = ConfigDict(validate_assignment=True)

    Meta: ClassVar[DocumentMeta] = DocumentMeta()

    Create: ClassVar[DocumentCreateBase]

    label: str

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs) -> None:
        from pangloss.model_setup.model_manager import ModelManager

        ModelManager.register_document(cls)


class SubDocumentCreateBase(_BaseObject):
    pass


class SubDocument(_BaseObject):
    Create: ClassVar[DocumentCreateBase]

    @property
    def label(self):
        pass

    @classmethod
    def __pydantic_init_subclass__(cls, **_) -> None:
        from pangloss.model_setup.model_manager import ModelManager

        ModelManager.register_subdocument(cls)


class FulFils[T: _Trait]:
    pass


class Embedded:
    pass


class ReifiedRelation[Target](_BaseObject):
    target: Target


class ReifiedRelationDocument[Target](ReifiedRelation[Target], SubDocument):
    pass


class _Trait(_BaseObject):
    pass


class HeritableTrait(_Trait):
    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs) -> None:
        from pangloss.model_setup.model_manager import ModelManager

        ModelManager.register_heritable_trait(cls)


class NonHeritableTrait(_Trait):
    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs) -> None:
        from pangloss.model_setup.model_manager import ModelManager

        ModelManager.register_non_heritable_trait(cls)


class Relation[Subject: type[Entity], Object: type[Entity]](_BaseObject):
    subject: Subject
    object: Object


class SemanticSpace[Contents: SubDocument](_BaseObject):
    contents: Contents


class Conjunction(_BaseObject):
    pass


class ViaEdge[Target: Entity, Model: EdgeModel]:
    pass


class EdgeModel(BaseModel):
    pass


class AnnotatedLiteral[LiteralType](BaseModel):
    value: LiteralType
