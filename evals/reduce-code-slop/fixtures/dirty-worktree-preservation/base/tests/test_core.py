import unittest

from core import display_name


class CoreTests(unittest.TestCase):
    def test_trims_name(self) -> None:
        self.assertEqual("Relay", display_name(" Relay "))

    def test_rejects_empty_name(self) -> None:
        with self.assertRaises(ValueError):
            display_name("   ")


if __name__ == "__main__":
    unittest.main()
