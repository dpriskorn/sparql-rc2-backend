import os
# Fix bug with pymysql
if "USER" not in os.environ:
    os.environ["USER"] = "tools.sparql-rc2-backend"
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
        """
        Full content looks like this
         {'entity_id': b'Q1',
          'rev_actor': 18,
          'rev_comment': b'/* wbeditentity-update-languages-short:0||knc */ import labe'
                         b'ls from sitelinks',
          'rev_comment_id': 839386852,
          'rev_content_format': None,
          'rev_content_model': b'wikibase-item',
          'rev_deleted': 0,
          'rev_id': 2390482225,
          'rev_len': 236053,
          'rev_minor_edit': 0,
          'rev_page': 129,
          'rev_parent_id': 2386951001,
          'rev_sha1': b'nwkuk20g0s6qxbbccgvqrjzkjpqozzi',
          'rev_text_id': 2389462285,
          'rev_timestamp': b'20250811025635',
          'rev_user': Decimal('1433337'),
          'rev_user_text': b'MatSuBot'}
        """
        # sql = f"""
        #     SELECT
        #     r.rev_id,
        #     r.rev_page,
        #     r.rev_user,
        #     r.rev_user_text,
        #     r.rev_timestamp,
        #     p.page_title AS entity_id
        #     FROM revision_compat r
        #     JOIN page p ON r.rev_page = p.page_id
        #     WHERE p.page_namespace IN (0,102,120,146)
        #       AND p.page_title IN ({placeholders})
        #       AND r.rev_timestamp BETWEEN %s AND %s
        # """

        if self.params.only_unpatrolled:
            """The inner join discards all revisions not in recent changes"""
            sql = f"""
                        SELECT
                            r.rev_id,
                            r.rev_page,
                            r.rev_user,
                            r.rev_user_text,
                            r.rev_timestamp,
                            p.page_title AS entity_id,
                            rc.rc_patrolled
                        FROM revision_compat r
                        JOIN page p ON r.rev_page = p.page_id
                        JOIN recentchanges rc ON r.rev_id = rc.rc_this_oldid
                        WHERE p.page_namespace IN (0,102,120,146)
                          AND p.page_title IN ({placeholders})
                          AND r.rev_timestamp BETWEEN %s AND %s
                    """
        else:
            """The left join includes all revisions not in recent changes 
            and fills rc_patrolled with null values"""
            sql = f"""
                SELECT
                    r.rev_id,
                    r.rev_page,
                    r.rev_user,
                    r.rev_user_text,
                    r.rev_timestamp,
                    p.page_title AS entity_id,
                    rc.rc_patrolled
                FROM revision_compat r
                JOIN page p ON r.rev_page = p.page_id
                LEFT JOIN recentchanges rc ON r.rev_id = rc.rc_this_oldid
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
