import unittest
from datetime import datetime, timezone

from app import available_handlers
from wrappers import current_timestamp


class ContractTests(unittest.TestCase):
    def test_registration_and_clock_seam(self) -> None:
        self.assertEqual(available_handlers(), ["csv"])
        fixed = datetime(2026, 1, 1, tzinfo=timezone.utc)
        self.assertEqual(current_timestamp(lambda: fixed), fixed.isoformat())


if __name__ == "__main__":
    unittest.main()
