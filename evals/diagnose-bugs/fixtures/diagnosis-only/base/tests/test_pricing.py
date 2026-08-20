import unittest
from decimal import Decimal

from pricing import tax_total


class PricingTests(unittest.TestCase):
    def test_decimal_rounding_remains_decimal(self) -> None:
        self.assertEqual(tax_total(Decimal("10.05"), Decimal("0.20")), Decimal("2.01"))


if __name__ == "__main__":
    unittest.main()
