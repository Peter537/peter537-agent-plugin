import unittest

from orders import summarize_order


class OrderSummaryTests(unittest.TestCase):
    def test_counts_items(self) -> None:
        self.assertEqual(summarize_order([125, 375]), {"item_count": 2})

    def test_rejects_negative_amounts(self) -> None:
        with self.assertRaises(ValueError):
            summarize_order([125, -1])


if __name__ == "__main__":
    unittest.main()
