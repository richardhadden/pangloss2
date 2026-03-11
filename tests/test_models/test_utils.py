from pangloss.model_setup.model_bases.document import Document, DocumentMeta
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
