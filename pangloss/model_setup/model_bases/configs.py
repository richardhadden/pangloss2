from dataclasses import dataclass, field


@dataclass
class RelationConfig:
    reverse_name: str | None = None
    overrides_parent_fields: list = field(default_factory=list)

    def __post_init__(self):
        if self.reverse_name:
            self.reverse_name = self.reverse_name.lower().replace(" ", "_")


@dataclass
class DocumentFieldConfig(RelationConfig):
    pass


@dataclass
class EntityFieldConfig(RelationConfig):
    pass
