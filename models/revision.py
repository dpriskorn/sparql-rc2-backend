from pydantic import BaseModel


class Revision(BaseModel):
    """
    rc_patrolled: now has three states:
        "0" for unpatrolled,
        "1" for manually patrolled
        "2" for autopatrolled actions
    see https://www.mediawiki.org/wiki/Manual:Recentchanges_table#rc_patrolled
    """

    rev_id: int
    rev_page: int
    rev_user: int
    rev_user_text: str
    rev_timestamp: str
    rc_patrolled: int | None = None

    @property
    def is_purged_from_recent_changes(self):
        if self.rc_patrolled is None:
            return True
        return False

    @property
    def is_manually_patrolled(self):
        if self.rc_patrolled == 1:
            return True
        return False

    @property
    def is_autopatrolled(self):
        if self.rc_patrolled == 2:
            return True
        return False

    @property
    def is_unpatrolled(self):
        if self.rc_patrolled == 0:
            return True
        return False
