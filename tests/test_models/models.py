from typing import Annotated

from pangloss.models import Document, DocumentFieldConfig, Entity, SubDocument


class Person(Entity):
    pass


class Factoid(Document):
    statements: Annotated[
        list[Statement], (DocumentFieldConfig(reverse_name="is_statement_in"))
    ]


class Statement(SubDocument):
    pass
