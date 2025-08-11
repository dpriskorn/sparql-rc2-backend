from unittest import TestCase

from models.aggregator import Aggregator
from models.revision import Revision


class TestAggregator(TestCase):
    def test_aggregate_single_revision(self):
        rows = [
            {
                "rev_page": 123,
                "rev_user": 1,
                "rev_user_text": "Alice",
                "rev_timestamp": "20220101000000",
                "entity_id": "Q1",
                "rev_id": 1,  # int now
            }
        ]
        aggregator = Aggregator(revisions=rows)
        result = aggregator.aggregate()

        assert len(result) == 1
        revs = result[0]
        assert revs.page_id == 123
        assert revs.entity_id == "Q1"
        assert isinstance(revs.earliest, Revision)
        assert isinstance(revs.latest, Revision)
        assert revs.earliest.rev_id == 1
        assert revs.latest.rev_id == 1
        assert len(revs.users) == 1
        user = revs.users[0]
        assert user.user_id == 1
        assert user.username == "Alice"
        assert user.count == 1

    def test_aggregate_multiple_revisions_same_page(self):
        rows = [
            {
                "rev_page": "123",
                "rev_user": "1",
                "rev_user_text": "Alice",
                "rev_timestamp": "20220101000000",
                "entity_id": "Q1",
                "rev_id": 1,
            },
            {
                "rev_page": "123",
                "rev_user": "2",
                "rev_user_text": "Bob",
                "rev_timestamp": "20220102000000",
                "entity_id": "Q1",
                "rev_id": 2,
            },
            {
                "rev_page": "123",
                "rev_user": "1",
                "rev_user_text": "Alice",
                "rev_timestamp": "20220103000000",
                "entity_id": "Q1",
                "rev_id": 3,
            },
        ]
        aggregator = Aggregator(revisions=rows)
        result = aggregator.aggregate()

        assert len(result) == 1
        revs = result[0]

        # Check earliest and latest revisions by timestamp
        assert revs.earliest.rev_id == 1
        assert revs.latest.rev_id == 3

        # Check users aggregated correctly
        user_counts = {u.username: u.count for u in revs.users}
        assert user_counts["Alice"] == 2
        assert user_counts["Bob"] == 1

    def test_aggregate_multiple_pages(self):
        rows = [
            {
                "rev_page": 123,
                "rev_user": 1,
                "rev_user_text": "Alice",
                "rev_timestamp": "20220101000000",
                "entity_id": "Q1",
                "rev_id": 1,
            },
            {
                "rev_page": 456,
                "rev_user": 2,
                "rev_user_text": "Bob",
                "rev_timestamp": "20220102000000",
                "entity_id": "Q2",
                "rev_id": 2,
            },
        ]
        aggregator = Aggregator(revisions=rows)
        result = aggregator.aggregate()

        assert len(result) == 2
        pages = {r.page_id: r for r in result}
        assert 123 in pages
        assert 456 in pages

        alice_rev = pages[123]
        bob_rev = pages[456]

        assert alice_rev.entity_id == "Q1"
        assert bob_rev.entity_id == "Q2"

        assert alice_rev.users[0].username == "Alice"
        assert alice_rev.users[0].count == 1

        assert bob_rev.users[0].username == "Bob"
        assert bob_rev.users[0].count == 1
