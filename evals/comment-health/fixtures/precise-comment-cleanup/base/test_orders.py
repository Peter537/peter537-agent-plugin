import unittest

from orders import normalize_code


class OrderTests(unittest.TestCase):
    def test_normalize_code(self) -> None:
        self.assertEqual(normalize_code(" ab-4 "), "AB-4")


if __name__ == "__main__":
    unittest.main()
