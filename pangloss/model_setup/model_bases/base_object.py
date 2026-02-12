from pydantic import BaseModel


class _BaseObject(BaseModel):
    @classmethod
    def _class_has_own_meta(cls):
        return "_meta" in cls.__dict__
