from pydantic import BaseModel


class UserCount(BaseModel):
    user_id: int
    username: str
    count: int
