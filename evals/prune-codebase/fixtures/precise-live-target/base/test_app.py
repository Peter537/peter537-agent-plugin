import unittest

from app import main


class AppTests(unittest.TestCase):
    def test_main_reports_health(self) -> None:
        self.assertEqual(main(), {"status": "ok"})


if __name__ == "__main__":
    unittest.main()
