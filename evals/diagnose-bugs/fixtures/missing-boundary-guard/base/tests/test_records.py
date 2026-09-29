import unittest
from records import parse_records


class RecordTests(unittest.TestCase):
    def test_newline_terminated_records(self):
        self.assertEqual(parse_records(" alpha \n\n beta \n"), ["alpha", "beta"])

    def test_empty(self):
        self.assertEqual(parse_records(""), [])
