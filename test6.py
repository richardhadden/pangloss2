from pydantic import BaseModel


class SemanticSpace[T](BaseModel):
    contents: list[T]


class Document(BaseModel):
    pass


class Entity(BaseModel):
    pass


class Negative[T](SemanticSpace[T]):
    pass


class Factoid(Document):
    statements: list[Negative[Order]]


class Action(Document):
    pass


class Order(Document):
    thing_ordered: Subjunctive[Action]


class Subjunctive[T](SemanticSpace[T]):
    pass


assert Factoid.model_fields["statements"]
