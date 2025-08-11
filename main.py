import logging
import os
from datetime import datetime, UTC, timedelta

from fastapi import FastAPI, Query

import config

if "USER" not in os.environ:
    os.environ["USER"] = "tools.sparql-rc2-backend"
import pymysql
from pymysql.cursors import DictCursor
from typing import List

from models.revision import Revision
from models.revisions import Revisions
from models.user_count import UserCount

logging.basicConfig(level=config.loglevel)
logger = logging.getLogger(__name__)

app = FastAPI()


# TOOL_NAME = "sparql-rc2-backend"


def get_db():
    logger.debug("get_db: running")

    return pymysql.connect(
        host="wikidatawiki.web.db.svc.wikimedia.cloud",
        user=os.environ.get("TOOL_REPLICA_USER"),
        password=os.environ.get("TOOL_REPLICA_PASSWORD"),
        database="wikidatawiki_p",
        charset="utf8mb4",
        cursorclass=DictCursor
    )


@app.get("/revisions", response_model=List[Revisions])
def get_revisions(
        entities: str = Query(..., description="Comma-separated list of entity IDs, e.g. Q42,L1 (currently does not support EID)"),
        start_date: str = Query(
            default=(datetime.now(tz=UTC) - timedelta(days=7)).strftime("%Y%m%d%H%M%S"),
            description="Start date in YYYYMMDDHHMMSS, defaults to one week ago"
        ),
        end_date: str = Query(
            default=datetime.now(tz=UTC).strftime("%Y%m%d%H%M%S"),
            description="End date in YYYYMMDDHHMMSS, defaults to now"
        ),
        no_bots: bool = Query(default=False, description="If true, revisions made by bot users are excluded.")
):
    """
    Get revision data for a list of Wikidata items within a given date range.

    - **items**: Comma-separated list of Wikidata item IDs (e.g., Q42,Q1).
    - **start_date**: Start of time interval (inclusive) in YYYYMMDDHHMMSS format. Defaults to one week ago.
    - **end_date**: End of time interval (inclusive) in YYYYMMDDHHMMSS format. Defaults to now.
    - **no_bots**: If true, revisions made by bot users are excluded.

    Returns a list of revisions info grouped by page_id, including earliest and latest revisions and user edit counts
    if there are any edits found within the timeframe.
    """
    # Gör om kommaseparerad sträng till lista
    entities_list = [i.strip() for i in entities.split(",") if i.strip()]

    db = get_db()
    cursor = db.cursor(DictCursor)

    placeholders = ",".join(["%s"] * len(entities_list))
    # 0=items 102=entityschema 120=properties 146=lexeme
    sql_page_ids = f"""
        SELECT DISTINCT page_id
        FROM page
        WHERE page_namespace IN (0,102,120,146)
        AND page_title IN ({placeholders})
    """

    sql_revisions = f"""
        SELECT * FROM revision_compat
        WHERE rev_page IN ({sql_page_ids})
        AND rev_timestamp BETWEEN %s AND %s
    """
    params = entities_list + [start_date, end_date]

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
