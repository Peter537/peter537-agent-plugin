import unittest

from tools.convert_v2 import convert


class ConverterTests(unittest.TestCase):
    def test_supported_conversion_is_idempotent(self):
        upgraded = convert({"schema_version": 1, "enabled": True})
        self.assertEqual(upgraded, {"schema_version": 2, "enabled": True})
        self.assertEqual(convert(upgraded), upgraded)
