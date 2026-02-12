from pydantic import BaseModel, Field


class RelationConfig(BaseModel):
    reverse_name: str
    overrides_parent_fields: list = Field(default_factory=list)


class DocumentFieldConfig(RelationConfig):
    pass
