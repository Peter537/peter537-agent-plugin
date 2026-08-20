import unittest

from parser import parse_setting


class ParserTests(unittest.TestCase):
    def test_setting(self) -> None:
        self.assertEqual(parse_setting("mode=safe"), ("mode", "safe"))


if __name__ == "__main__":
    unittest.main()
