from pydantic import BaseModel


class Splitter(BaseModel):
    entities_string: str
    entities: list[str] = []

    def split_entities(self):
        self.entities = [
            e.strip() for e in self.entities_string.split(",") if e.strip()
        ]
        # raise ValueError("entities must be a comma-separated string")
