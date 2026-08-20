import unittest

from checkout import checkout_total


class CheckoutTests(unittest.TestCase):
    def test_current_checkout(self) -> None:
        self.assertEqual(checkout_total([2, 4]), 6)


if __name__ == "__main__":
    unittest.main()
