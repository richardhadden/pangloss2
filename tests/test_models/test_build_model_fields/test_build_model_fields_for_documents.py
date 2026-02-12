from pangloss.models import Document


def test_initialise_model_definition_on_document():

    class Factoid(Document):
        name: str
