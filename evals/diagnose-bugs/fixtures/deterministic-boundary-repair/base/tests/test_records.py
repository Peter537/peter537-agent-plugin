import unittest

from records import parse_records


class RecordTests(unittest.TestCase):
    def test_preserves_every_nonempty_record(self) -> None:
        self.assertEqual(parse_records("alpha\nbeta\ngamma\n"), ["alpha", "beta", "gamma"])


if __name__ == "__main__":
    unittest.main()
