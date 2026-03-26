from typing import Generic, TypeVarTuple, get_args, get_origin

from pangloss.model_setup.model_bases.document import Document

Ts = TypeVarTuple("Ts")


class IfSatisfies(Generic[*Ts]):
    pass


class A(Document):
    pass


class B(Document):
    pass


print(get_origin(IfSatisfies[A, B]))
print(get_args(IfSatisfies[A, B]))
