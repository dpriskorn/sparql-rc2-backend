from fastapi import FastAPI
import pymysql
import os
from typing import List

from models.revision import Revision
from models.revisions import Revisions
from models.user_count import UserCount

app = FastAPI()


def get_db():
    return pymysql.connect(
        host="wikidata.db.svc.eqiad.wmflabs",
        user=os.environ["TOOLFORGE_USER"],
        password=os.environ["TOOLFORGE_PASSWORD"],
        database="wikidatawiki_p",
        charset="utf8mb4"
    )


@app.get("/revisions", response_model=List[Revisions])
def get_revisions(items: List[str], start_date: str, end_date: str, no_bots: bool = False):
    db = get_db()
    cursor = db.cursor(pymysql.cursors.DictCursor)

    placeholders = ",".join(["%s"] * len(items))
    sql_page_ids = f"""
        SELECT DISTINCT page_id
        FROM page
        WHERE page_namespace IN (0,146)
        AND page_title IN ({placeholders})
    """

    sql_revisions = f"""
        SELECT * FROM revision_compat
        WHERE rev_page IN ({sql_page_ids})
        AND rev_timestamp BETWEEN %s AND %s
    """
    params = items + [start_date, end_date]

    if no_bots:
        sql_revisions += """
            AND rev_user NOT IN (
                SELECT ug_user FROM user_groups WHERE ug_group='bot'
            )
        """

    cursor.execute(sql_revisions, params)
    rows = cursor.fetchall()

    temp = {}

    for o in rows:
        page_id = o["rev_page"]
        key = str(page_id)
        u_key = f"{o['rev_user']}|{o['rev_user_text']}"

        if key not in temp:
            temp[key] = {
                "page_id": page_id,
                "earliest": o.copy(),
                "latest": o.copy(),
                "note": "",
                "users": {u_key: 1}
            }
            continue

        if temp[key]["earliest"]["rev_timestamp"] > o["rev_timestamp"]:
            temp[key]["earliest"] = o.copy()

        if temp[key]["latest"]["rev_timestamp"] < o["rev_timestamp"]:
            temp[key]["latest"] = o.copy()

        temp[key]["users"][u_key] = temp[key]["users"].get(u_key, 0) + 1

    # Konvertera users-dict till lista av UserCount
    result = []
    for entry in temp.values():
        user_list = []
        for u_key, count in entry["users"].items():
            uid, uname = u_key.split("|", 1)
            user_list.append(UserCount(user_id=int(uid), username=uname, count=count))

        result.append(Revisions(
            page_id=entry["page_id"],
            earliest=Revision(**entry["earliest"]),
            latest=Revision(**entry["latest"]),
            note=entry["note"],
            users=user_list
        ))

    return result
