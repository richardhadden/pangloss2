from pangloss import initialise_models
from pangloss.model_setup.model_bases.document import DocumentMeta
from pangloss.models import Document


def test_initialise_meta_on_document():

    class Factoid(Document):
        _meta = DocumentMeta(abstract=False)

    class DatedFactoid(Factoid):
        pass

    class DatedFactoid2(DatedFactoid):
        _meta = DocumentMeta(abstract=True, create_with_id=True)

    class DatedFactoid3(DatedFactoid):
        _meta = DocumentMeta()

    initialise_models()

    # assert DatedFactoid._meta.abstract is False
    # assert DatedFactoid2._meta.abstract is True

    # assert DatedFactoid3._meta.abstract is False
    # assert DatedFactoid3._meta.create_with_id is True
