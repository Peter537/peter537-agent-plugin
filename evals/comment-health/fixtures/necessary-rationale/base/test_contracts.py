import unittest

from money import cents_to_display_units
from security import token_matches


class ContractTests(unittest.TestCase):
    def test_units_and_comparison(self) -> None:
        self.assertEqual(cents_to_display_units(105), "1.05")
        self.assertTrue(token_matches(b"same", b"same"))
        self.assertFalse(token_matches(b"one", b"two"))


if __name__ == "__main__":
    unittest.main()
