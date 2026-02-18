from pangloss.model_setup.model_bases.base_object import _DeclaredClass
from pangloss.model_setup.model_bases.entity import Entity


class Relation[Subject: type[Entity], Object: type[Entity]](_DeclaredClass):
    subject: Subject
    object: Object
