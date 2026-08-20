import unittest

from converter import convert


class ConverterTests(unittest.TestCase):
    def test_converts_file(self) -> None:
        self.assertEqual(convert("sample.txt"), "HELLO\n")


if __name__ == "__main__":
    unittest.main()
