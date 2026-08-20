import unittest

from library import request


class LibraryTests(unittest.TestCase):
    def test_default_retry_count(self) -> None:
        self.assertEqual(request("https://example.invalid"), ("https://example.invalid", 3))


if __name__ == "__main__":
    unittest.main()
