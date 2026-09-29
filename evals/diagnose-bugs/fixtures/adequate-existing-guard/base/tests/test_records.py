import unittest
from records import parse_records


class RecordTests(unittest.TestCase):
    def test_supported_record_inputs(self):
        examples = (("", []), ("  \n\n", []), ("alpha", ["alpha"]),
                    ("alpha\n", ["alpha"]), ("alpha\nbeta", ["alpha", "beta"]),
                    (" alpha \n\n beta \n", ["alpha", "beta"]))
        for text, expected in examples:
            with self.subTest(text=text):
                self.assertEqual(parse_records(text), expected)
