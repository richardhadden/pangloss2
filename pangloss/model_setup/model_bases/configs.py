from dataclasses import dataclass, field


@dataclass
class RelationConfig:
    reverse_name: str
    overrides_parent_fields: list = field(default_factory=list)


@dataclass
class DocumentFieldConfig(RelationConfig):
    pass


@dataclass
class EntityFieldConfig(RelationConfig):
    pass
