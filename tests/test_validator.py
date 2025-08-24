import re
import unittest
from unittest.mock import patch

from pydantic import ValidationError

from models.validator import Validator


class TestValidator(unittest.TestCase):
    def setUp(self):
        # Mock config values
        self.patcher_max = patch("config.MAX_ENTITY_COUNT", 3)
        self.patcher_pattern = patch("config.ENTITY_ID_PATTERN", re.compile(r"^Q\d+$"))
        self.patcher_timestamp = patch(
            "config.TIMESTAMP_PATTERN", re.compile(r"^\d{8}$")
        )

        self.mock_max = self.patcher_max.start()
        self.mock_id_pattern = self.patcher_pattern.start()
        self.mock_timestamp_pattern = self.patcher_timestamp.start()

    def tearDown(self):
        patch.stopall()

    def test_valid_input(self):
        v = Validator(
            entities=["Q1", "Q2"],
            start_date="20230101",
            end_date="20231231",
            no_bots=True,
        )
        self.assertEqual(v.entities, ["Q1", "Q2"])
        self.assertEqual(v.start_date, "20230101")
        self.assertEqual(v.end_date, "20231231")
        self.assertTrue(v.no_bots)

    def test_not_unique(self):
        with self.assertRaises(ValidationError) as cm:
            Validator(
                entities=["Q1", "Q1"],
                start_date="20230101",
                end_date="20231231",
                no_bots=True,
            )
        # Optionally check the error message contains the uniqueness error
        self.assertIn("Entity IDs must be unique", str(cm.exception))

    def test_too_many_entities(self):
        with self.assertRaises(ValidationError):
            Validator(
                entities=["Q1", "Q2", "Q3", "Q4"],
                start_date="20230101",
                end_date="20231231",
            )
        # self.assertIn("Too many entity IDs", str(cm.exception))

    def test_invalid_entity_id(self):
        with self.assertRaises(ValidationError):
            Validator(entities=["Q1", "X2"], start_date="20230101", end_date="20231231")

    def test_invalid_start_date_format(self):
        with self.assertRaises(ValidationError) as cm:
            Validator(entities=["Q1"], start_date="2023-01-01", end_date="20231231")
        self.assertIn("Invalid start_date format", str(cm.exception))

    def test_invalid_end_date_format(self):
        with self.assertRaises(ValidationError) as cm:
            Validator(entities=["Q1"], start_date="20230101", end_date="2023-12-31")
        self.assertIn("Invalid end_date format", str(cm.exception))

    def test_start_date_after_end_date(self):
        with self.assertRaises(ValidationError) as cm:
            Validator(entities=["Q1"], start_date="20231231", end_date="20230101")
        self.assertIn(
            "start_date must be earlier than or equal to end_date", str(cm.exception)
        )

    def test_start_date_equal_end_date(self):
        v = Validator(entities=["Q1"], start_date="20230101", end_date="20230101")
        self.assertEqual(v.start_date, "20230101")
        self.assertEqual(v.end_date, "20230101")
