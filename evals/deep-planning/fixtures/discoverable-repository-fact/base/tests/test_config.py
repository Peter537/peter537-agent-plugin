from pathlib import Path
import unittest


class ConfigTests(unittest.TestCase):
    def test_configuration_exists(self):
        self.assertIn("line_width", Path("pyproject.toml").read_text(encoding="utf-8"))
