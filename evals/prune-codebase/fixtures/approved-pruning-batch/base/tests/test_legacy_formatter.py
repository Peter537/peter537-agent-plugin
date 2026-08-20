import unittest

from legacy_formatter import format_total_legacy


class LegacyFormatterTests(unittest.TestCase):
    def test_total(self) -> None:
        self.assertEqual(format_total_legacy(4), "Legacy total: 4")


if __name__ == "__main__":
    unittest.main()
