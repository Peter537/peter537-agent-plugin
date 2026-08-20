import unittest

from app import render


class RenderTests(unittest.TestCase):
    def test_appends_newline(self) -> None:
        self.assertEqual(render("hello"), "hello\n")


if __name__ == "__main__":
    unittest.main()
