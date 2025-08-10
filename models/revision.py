from pydantic import BaseModel


class Revision(BaseModel):
    rev_id: int
    rev_page: int
    rev_user: int
    rev_user_text: str
    rev_timestamp: str



