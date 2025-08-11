from pydantic import BaseModel, field_validator


class Splitter(BaseModel):
    entities: list[str] | str  # accepts either raw string or list

    # noinspection PyMethodParameters
    @field_validator("entities", mode="before")
    def split_entities(cls, v):
        if isinstance(v, str):
            return [e.strip() for e in v.split(",") if e.strip()]
        if isinstance(v, list):
            return v
        raise ValueError("entities must be a comma-separated string or list of strings")
