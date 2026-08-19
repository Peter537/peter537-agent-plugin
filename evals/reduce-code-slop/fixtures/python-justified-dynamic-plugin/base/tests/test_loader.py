import unittest

from loader import load_factory


class LoaderTests(unittest.TestCase):
    def test_loads_external_coordinate(self) -> None:
        self.assertEqual("example", load_factory("plugins.example:factory").create())

    def test_rejects_invalid_coordinate(self) -> None:
        with self.assertRaises(ValueError):
            load_factory("plugins.example")


if __name__ == "__main__":
    unittest.main()
