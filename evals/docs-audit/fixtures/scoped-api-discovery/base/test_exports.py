import unittest
from exports import export_rows
class ExportTests(unittest.TestCase):
    def test_export(self):
        self.assertEqual(export_rows([[1, 2]]), "1,2")
