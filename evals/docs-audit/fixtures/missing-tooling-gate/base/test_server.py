import unittest

from server import parser


class ServerCliTests(unittest.TestCase):
    def test_bind_flag(self) -> None:
        self.assertEqual(parser().parse_args(["--bind", "localhost"]).bind, "localhost")


if __name__ == "__main__":
    unittest.main()
