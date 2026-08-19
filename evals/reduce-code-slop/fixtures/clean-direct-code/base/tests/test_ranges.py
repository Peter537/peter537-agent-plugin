import unittest

from ranges import clamp


class RangeTests(unittest.TestCase):
    def test_clamps_inside_and_outside_bounds(self) -> None:
        self.assertEqual(5, clamp(5, 0, 10))
        self.assertEqual(0, clamp(-2, 0, 10))
        self.assertEqual(10, clamp(14, 0, 10))

    def test_rejects_reversed_bounds(self) -> None:
        with self.assertRaises(ValueError):
            clamp(1, 4, 2)


if __name__ == "__main__":
    unittest.main()
