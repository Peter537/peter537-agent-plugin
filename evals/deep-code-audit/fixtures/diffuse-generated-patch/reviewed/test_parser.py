import unittest

from parser import parse_assignment


class ParserTests(unittest.TestCase):
    def test_parses_assignment(self) -> None:
        self.assertEqual(parse_assignment("color=blue"), ("color", "blue"))

    def test_trims_whitespace_around_both_fields(self) -> None:
        self.assertEqual(parse_assignment(" color = blue "), ("color", "blue"))

    def test_rejects_lines_without_separator(self) -> None:
        with self.assertRaises(ValueError):
            parse_assignment("color")


if __name__ == "__main__":
    unittest.main()
