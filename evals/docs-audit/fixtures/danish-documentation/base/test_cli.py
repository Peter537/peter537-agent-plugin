import unittest

from cli import parser


class CliTests(unittest.TestCase):
    def test_input_flag(self) -> None:
        self.assertEqual(parser().parse_args(["--input", "poster.json"]).input, "poster.json")


if __name__ == "__main__":
    unittest.main()
