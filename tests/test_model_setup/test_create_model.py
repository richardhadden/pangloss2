from typing import no_type_check
from uuid import UUID, uuid7

from pydantic import AnyHttpUrl

from pangloss.model_setup.model_bases.document import Document


def test_create_model_for_document_with_no_id():
    class Statement(Document):
        name: str

    assert Statement.Create
    assert "id" not in Statement.Create.model_fields


@no_type_check
def test_create_model_for_document_with_id_allowed():
    class Statement(Document):
        _meta = Document.Meta(create_with_id=True)
        name: str

    assert Statement.Create
    assert "id" in Statement.Create.model_fields

    id_field = Statement.Create.model_fields["id"]

    assert id_field.annotation == UUID | None

    st = Statement.Create(id=uuid7(), create_new=True)
    assert isinstance(st.id, UUID)
    assert st.create_new


@no_type_check
def test_create_model_for_document_with_id_and_url_allowed():
    class Statement(Document):
        _meta = Document.Meta(create_with_id=True, accept_url_as_id=True)
        name: str

    assert Statement.Create
    assert "id" in Statement.Create.model_fields

    id_field = Statement.Create.model_fields["id"]

    assert id_field.annotation == UUID | AnyHttpUrl | None

    st = Statement.Create(id="http://test.com/statement1", create_new=True)
    assert isinstance(st.id, AnyHttpUrl)
    assert st.create_new
