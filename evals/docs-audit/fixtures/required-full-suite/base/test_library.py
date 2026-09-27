import unittest
from library import request_options
class LibraryTests(unittest.TestCase):
    def test_default(self):
        self.assertEqual(request_options("https://example.invalid"), {"url": "https://example.invalid", "retries": 3})
