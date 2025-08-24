from pydantic import BaseModel


class Splitter(BaseModel):
    string: str
    list_: list[str] = []

    def split_comma_separated_string(self):
        self.list_ = [e.strip() for e in self.string.split(",") if e.strip()]
        # raise ValueError("entities must be a comma-separated string")
