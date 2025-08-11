import logging
import os
from datetime import datetime, UTC, timedelta

from fastapi import FastAPI, Query
from fastapi.responses import RedirectResponse

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


@app.get("/", include_in_schema=False)  # Don't include in the API docs
def root_redirect():
    # Redirect to the built-in FastAPI Swagger docs
    return RedirectResponse(url="/docs")


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
    sql_revisions = f"""
        SELECT r.*, p.page_title AS entity_id
        FROM revision_compat r
        JOIN page p
            ON r.rev_page = p.page_id
        WHERE p.page_namespace IN (0,102,120,146)
          AND p.page_title IN ({placeholders})
          AND r.rev_timestamp BETWEEN %s AND %s
    """
    params = entities_list + [start_date, end_date]

    if no_bots:
        sql_revisions += """
            AND r.rev_user NOT IN (
                SELECT ug_user FROM user_groups WHERE ug_group='bot'
            )
        """

    cursor.execute(sql_revisions, params)
    rows = cursor.fetchall()

    revisions_by_page = {}

    for revision in rows:
        # Extract the page ID for the current revision
        page_id = revision["rev_page"]

        # Use string form of page_id as dictionary key (dict keys must be hashable and comparable)
        page_key = str(page_id)

        # Create a unique identifier for the user, combining ID and username
        user_key = f"{revision['rev_user']}|{revision['rev_user_text']}"

        # If this page hasn't been seen before, initialize its entry
        if page_key not in revisions_by_page:
            revisions_by_page[page_key] = {
                "page_id": page_id,  # Numeric page ID
                "entity_id": revision["entity_id"],  # Wikidata entity ID (e.g., Q42, L1)
                "earliest": revision.copy(),  # Earliest revision found so far (start with current one)
                "latest": revision.copy(),  # Latest revision found so far (start with current one)
                "note": "",  # Placeholder for any notes
                "users": {user_key: 1}  # Dict of users and their edit counts (start with 1)
            }
            continue  # Skip to next revision since initialization is done

        # Update earliest revision if the current revision is older (smaller timestamp)
        if revisions_by_page[page_key]["earliest"]["rev_timestamp"] > revision["rev_timestamp"]:
            revisions_by_page[page_key]["earliest"] = revision.copy()

        # Update latest revision if the current revision is newer (larger timestamp)
        if revisions_by_page[page_key]["latest"]["rev_timestamp"] < revision["rev_timestamp"]:
            revisions_by_page[page_key]["latest"] = revision.copy()

        # Increment the edit count for this user on the current page
        revisions_by_page[page_key]["users"][user_key] = (
                revisions_by_page[page_key]["users"].get(user_key, 0) + 1
        )

    # Convert the "users" dictionary for each page into a list of UserCount objects
    result = []

    # Iterate over each page's collected revision data
    for page_data in revisions_by_page.values():
        user_list = []

        # Go through all users who edited this page and their edit counts
        for user_key, count in page_data["users"].items():
            # Split the combined "user_id|username" string back into ID and username
            user_id_str, username = user_key.split("|", 1)

            # Create a UserCount object and add it to the list
            user_list.append(
                UserCount(user_id=int(user_id_str), username=username, count=count)
            )

        result.append(
            Revisions(
                page_id=page_data["page_id"],
                entity_id=page_data["entity_id"],
                earliest=Revision(**page_data["earliest"]),
                latest=Revision(**page_data["latest"]),
                note=page_data["note"],
                users=user_list
            )
        )

    return result
