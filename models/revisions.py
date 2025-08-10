from typing import List
from pydantic import BaseModel

from models.revision import Revision
from models.user_count import UserCount


class Revisions(BaseModel):
    page_id: int
    earliest: Revision
    latest: Revision
    note: str
    users: List[UserCount]
