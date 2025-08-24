from pydantic import BaseModel, field_validator, model_validator

import config


class Validator(BaseModel):
    entities: list[str]
    start_date: str
    end_date: str
    no_bots: bool = False
    only_unpatrolled: bool = False
    exclude_users: list[str] = []

    # noinspection PyMethodParameters
    @field_validator("entities")
    def validate_entities(cls, v):
        if len(v) > config.MAX_ENTITY_COUNT:
            raise ValueError(f"Too many entity IDs (max {config.MAX_ENTITY_COUNT})")
        if len(v) != len(set(v)):
            raise ValueError("Entity IDs must be unique (no duplicates)")
        for eid in v:
            if not config.ENTITY_ID_PATTERN.match(eid):
                raise ValueError(f"Invalid entity ID: {eid}")
        return v

    # noinspection PyMethodParameters
    @field_validator("start_date", "end_date")
    def validate_timestamp_format(cls, v, info):
        if not config.TIMESTAMP_PATTERN.match(v):
            raise ValueError(f"Invalid {info.field_name} format: {v}")
        return v

    # noinspection PyMethodParameters
    @model_validator(mode="after")
    def check_dates_order(cls, values):
        start = values.start_date
        end = values.end_date
        if start and end and start > end:
            raise ValueError("start_date must be earlier than or equal to end_date")
        return values
