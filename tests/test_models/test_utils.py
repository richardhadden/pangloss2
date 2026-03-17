import datetime

from pangloss.model_setup.model_bases.document import Document, DocumentMeta
from pangloss.model_setup.model_bases.embedded import Embedded, EmbeddedMeta
from pangloss.model_setup.utils import generic_get_subclasses, get_concrete_types


def test_get_generic_subclasses():
    class Statement(Document):
        pass

    class Action(Statement):
        pass

    class CreationOfArtwork(Action):
        pass

    class CreationOfPainting(CreationOfArtwork):
        pass

    assert generic_get_subclasses(Statement) == set(
        [Action, CreationOfArtwork, CreationOfPainting]
    )


def test_get_concrete_types_simple():
    class Statement(Document):
        pass

    class Other(Document):
        pass

    class Action(Statement):
        pass

    class CreationOfArtwork(Action):
        _meta = DocumentMeta(abstract=True)

    class CreationOfPainting(CreationOfArtwork):
        pass

    assert get_concrete_types(Statement) == set([Statement, Action, CreationOfPainting])

    assert get_concrete_types(Statement, include_abstract=True) == set(
        [Statement, Action, CreationOfArtwork, CreationOfPainting]
    )

    # Throw in a union type here to check it works
    assert get_concrete_types(Statement | Other) == set(
        [Statement, Action, CreationOfPainting, Other]
    )


def test_get_concrete_types_with_abstract():
    class Statement(Document):
        _meta = DocumentMeta(abstract=True)

    class Thing(Statement):
        pass

    assert get_concrete_types(Statement) == set([Thing])


def test_get_concrete_types_with_abstract_in_union():
    class Statement(Document):
        _meta = DocumentMeta(abstract=True)

    class Thing(Document):
        pass

    assert get_concrete_types(Statement | Thing) == set([Thing])


def test_get_concrete_types_with_embedded_abstract_in_union():
    class Date(Embedded):
        _meta = EmbeddedMeta(abstract=True)
        when: datetime.datetime

    class Statement(Document):
        date: Date

    class SpecialDate(Date):
        pass

    assert get_concrete_types(Date) == set([SpecialDate])
    assert get_concrete_types(SpecialDate) == set([SpecialDate])
    assert get_concrete_types(Date | SpecialDate) == set([SpecialDate])
