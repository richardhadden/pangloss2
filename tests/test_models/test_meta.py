from pangloss.model_setup.model_bases.document import Document, DocumentMeta


def test_meta_inheritance_of_abstract():
    class Statement(Document):
        _meta = DocumentMeta(abstract=True)

    class Action(Statement):
        pass

    class CreationOfArtwork(Action):
        _meta = DocumentMeta(abstract=True)

    class CreationOfPainting(CreationOfArtwork):
        pass

    assert Statement._meta.abstract is True
    assert Action._meta.abstract is False
    assert CreationOfArtwork._meta._owner_class is CreationOfArtwork
    assert CreationOfArtwork._meta.abstract is True
    assert CreationOfPainting._meta.abstract is False
