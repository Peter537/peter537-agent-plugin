import unittest

from wrapper import calculate_total


class WrapperTests(unittest.TestCase):
    def test_total(self) -> None:
        self.assertEqual(7, calculate_total([2, 5]))

    def test_rejects_negative_values(self) -> None:
        with self.assertRaises(ValueError):
            calculate_total([2, -1])


if __name__ == "__main__":
    unittest.main()
