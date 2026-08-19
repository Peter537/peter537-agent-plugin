import unittest

from formatter import format_message


class FormatterTests(unittest.TestCase):
    def test_formats_the_supported_message(self) -> None:
        self.assertEqual(format_message(" Status ", " Ready "), "Status: Ready")

    def test_rejects_empty_fields(self) -> None:
        with self.assertRaises(ValueError):
            format_message("", "Ready")


if __name__ == "__main__":
    unittest.main()
