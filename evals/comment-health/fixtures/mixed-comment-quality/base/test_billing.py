import unittest

from billing import calculate_total


class BillingTests(unittest.TestCase):
    def test_discount_begins_after_five_years(self) -> None:
        self.assertEqual(calculate_total(1_000, 4), 1_000)
        self.assertEqual(calculate_total(1_000, 5), 900)


if __name__ == "__main__":
    unittest.main()
