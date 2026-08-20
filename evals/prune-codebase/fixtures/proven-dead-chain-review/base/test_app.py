import unittest

from app import current_report


class AppTests(unittest.TestCase):
    def test_current_report(self) -> None:
        self.assertEqual(current_report([1, 2, 3]), 6)


if __name__ == "__main__":
    unittest.main()
