import unittest

from normalizer import normalize


class NormalizeTests(unittest.TestCase):
    def test_collapses_internal_whitespace(self) -> None:
        self.assertEqual(normalize("  Alpha   Beta  "), "alpha beta")


if __name__ == "__main__":
    unittest.main()
