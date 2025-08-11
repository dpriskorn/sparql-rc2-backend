import os
import pymysql
from pydantic import BaseModel
from pymysql.connections import Connection
from pymysql.cursors import DictCursor
from models.validator import Validator  # your Pydantic model


class Read(BaseModel):
    params: Validator
    db: None | Connection = None

    class Config:
        arbitrary_types_allowed = True

    def connect(self):
        # Opens a new DB connection and assigns to self.db
        if self.db is None:
            self.db = pymysql.connect(
                host="wikidatawiki.web.db.svc.wikimedia.cloud",
                user=os.environ.get("TOOL_REPLICA_USER"),
                password=os.environ.get("TOOL_REPLICA_PASSWORD"),
                database="wikidatawiki_p",
                charset="utf8mb4",
                cursorclass=DictCursor,
            )
        return self.db

    def fetch_revisions(self):
        # Make sure we have a DB connection
        self.connect()

        cursor = self.db.cursor()
        placeholders = ",".join(["%s"] * len(self.params.entities))
        sql = f"""
            SELECT r.*, p.page_title AS entity_id
            FROM revision_compat r
            JOIN page p ON r.rev_page = p.page_id
            WHERE p.page_namespace IN (0,102,120,146)
              AND p.page_title IN ({placeholders})
              AND r.rev_timestamp BETWEEN %s AND %s
        """
        params_list = self.params.entities + [self.params.start_date, self.params.end_date]

        if self.params.no_bots:
            sql += """
                AND r.rev_user NOT IN (
                    SELECT ug_user FROM user_groups WHERE ug_group='bot'
                )
            """

        cursor.execute(sql, params_list)
        return cursor.fetchall()

    def close(self):
        if self.db:
            self.db.close()
            self.db = None
