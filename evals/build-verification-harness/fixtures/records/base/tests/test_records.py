import unittest
from records import parse_records


class RecordTests(unittest.TestCase):
    def test_records(self):
        self.assertIsInstance(parse_records(" alpha \n\n beta"), list)
