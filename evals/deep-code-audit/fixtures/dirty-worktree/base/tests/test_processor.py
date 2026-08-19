import unittest

from core.processor import average


class ProcessorTests(unittest.TestCase):
    def test_average_for_integral_result(self) -> None:
        self.assertEqual(average([2, 4]), 3.0)

    def test_empty_input_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            average([])


if __name__ == "__main__":
    unittest.main()
