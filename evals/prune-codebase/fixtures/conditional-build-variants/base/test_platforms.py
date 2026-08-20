import unittest

from platform_loader import load_separator


class PlatformTests(unittest.TestCase):
    def test_every_declared_variant(self) -> None:
        self.assertEqual(load_separator("linux"), "/")
        self.assertEqual(load_separator("windows"), "\\")


if __name__ == "__main__":
    unittest.main()
