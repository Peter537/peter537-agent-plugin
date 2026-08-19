import unittest

from ranges import clamp, contains


class RangeTests(unittest.TestCase):
    def test_clamp_preserves_values_inside_the_range(self) -> None:
        self.assertEqual(clamp(5, 1, 10), 5)

    def test_clamp_applies_both_bounds(self) -> None:
        self.assertEqual(clamp(-2, 1, 10), 1)
        self.assertEqual(clamp(14, 1, 10), 10)

    def test_contains_uses_inclusive_bounds(self) -> None:
        self.assertTrue(contains(1, 1, 10))
        self.assertTrue(contains(10, 1, 10))
        self.assertFalse(contains(11, 1, 10))

    def test_invalid_bounds_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            clamp(5, 10, 1)
        with self.assertRaises(ValueError):
            contains(5, 10, 1)


if __name__ == "__main__":
    unittest.main()
