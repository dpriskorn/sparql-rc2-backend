import unittest

from pydantic import ValidationError

from models.splitter import Splitter


# noinspection PyTypeChecker
class TestSplitter(unittest.TestCase):
    def test_splitter_with_comma_separated_string(self):
        s = Splitter(entities_string="Q42, L1 ,Q99")
        s.split_entities()
        self.assertEqual(s.entities, ["Q42", "L1", "Q99"])

    # def test_splitter_with_list_of_strings(self):
    #     s = Splitter(entities_string="Q42, L1, Q99")
    #     s.split_entities()
    #     self.assertEqual(s.entities, ["Q42", "L1", "Q99"])

    def test_splitter_with_empty_string(self):
        s = Splitter(entities_string="")
        s.split_entities()
        self.assertEqual(s.entities, [])

    def test_splitter_with_whitespace_and_commas(self):
        s = Splitter(entities_string="  Q42 , , L1 ,, Q99 ")
        s.split_entities()
        self.assertEqual(s.entities, ["Q42", "L1", "Q99"])

    def test_splitter_with_invalid_type(self):
        with self.assertRaises(ValidationError):
            Splitter(entities_string=123)  # type:ignore

    def test_splitter_with_none(self):
        with self.assertRaises(ValidationError):
            Splitter(entities_string=None)  # type:ignore
