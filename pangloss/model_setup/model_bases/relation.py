from pangloss.model_setup.model_bases.base_object import _BaseObject
from pangloss.model_setup.model_bases.entity import Entity


class Relation[Subject: type[Entity], Object: type[Entity]](_BaseObject):
    subject: Subject
    object: Object
