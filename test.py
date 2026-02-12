class Root:
    pass


class Document(Root):
    pass


class Mixin:
    def __init_subclass__(cls) -> None:
        print(cls.__bases__)


class Thing(Document, Mixin):
    pass
