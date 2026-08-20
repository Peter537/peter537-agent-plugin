import unittest

from tools.convert_v2 import convert


class ConverterTests(unittest.TestCase):
    def test_converter_is_repeatable(self) -> None:
        once = convert({"schema_version": 1})
        self.assertEqual(convert(once), once)


if __name__ == "__main__":
    unittest.main()
