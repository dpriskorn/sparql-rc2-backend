from typing import Dict, List

from pydantic import BaseModel

from models.revision import Revision
from models.revisions import Revisions
from models.user_count import UserCount


class Aggregator(BaseModel):
    revisions: List[Dict[str, str | int]]

    def aggregate(self):
        revisions_by_page = {}
        for revision in self.revisions:
            page_key = str(revision["rev_page"])
            user_key = f"{revision['rev_user']}|{revision['rev_user_text']}"

            if page_key not in revisions_by_page:
                revisions_by_page[page_key] = {
                    "page_id": revision["rev_page"],
                    "entity_id": revision["entity_id"],
                    "earliest": revision.copy(),
                    "latest": revision.copy(),
                    "note": "",
                    "users": {user_key: 1},
                }
                continue

            if revisions_by_page[page_key]["earliest"]["rev_timestamp"] > revision["rev_timestamp"]:
                revisions_by_page[page_key]["earliest"] = revision.copy()
            if revisions_by_page[page_key]["latest"]["rev_timestamp"] < revision["rev_timestamp"]:
                revisions_by_page[page_key]["latest"] = revision.copy()

            revisions_by_page[page_key]["users"][user_key] = revisions_by_page[page_key]["users"].get(user_key, 0) + 1

        result = []
        for page_data in revisions_by_page.values():
            users = [
                UserCount(user_id=int(uid), username=uname, count=count)
                for uid, uname, count in (
                    (u.split("|", 1)[0], u.split("|", 1)[1], c) for u, c in page_data["users"].items()
                )
            ]

            result.append(
                Revisions(
                    page_id=page_data["page_id"],
                    entity_id=page_data["entity_id"],
                    earliest=Revision(**page_data["earliest"]),
                    latest=Revision(**page_data["latest"]),
                    note=page_data["note"],
                    users=users,
                )
            )
        return result
