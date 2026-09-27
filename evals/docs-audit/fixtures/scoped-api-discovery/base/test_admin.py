import unittest
from admin import display_user
class AdminTests(unittest.TestCase):
    def test_display(self):
        self.assertEqual(display_user({"name": "fixture"}), "fixture")
