import unittest

from active_formatter import format_total


class ActiveFormatterTests(unittest.TestCase):
    def test_total(self) -> None:
        self.assertEqual(format_total(4), "Total: 4")


if __name__ == "__main__":
    unittest.main()
