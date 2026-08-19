import unittest

from module import label


class ModuleTests(unittest.TestCase):
    def test_label(self) -> None:
        self.assertEqual("ready", label(" ready "))


if __name__ == "__main__":
    unittest.main()
