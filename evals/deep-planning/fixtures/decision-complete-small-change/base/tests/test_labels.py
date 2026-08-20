import unittest
from labels import archive_label


class LabelTests(unittest.TestCase):
    def test_label(self):
        self.assertEqual(archive_label(), "Archive")
