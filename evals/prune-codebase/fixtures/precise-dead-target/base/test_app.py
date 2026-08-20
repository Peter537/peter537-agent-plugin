import unittest

from app import main


class AppTests(unittest.TestCase):
    def test_main_returns_active_status(self) -> None:
        self.assertEqual(main(), "active")


if __name__ == "__main__":
    unittest.main()
