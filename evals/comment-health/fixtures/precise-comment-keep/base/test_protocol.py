import unittest

from protocol import encode_length


class ProtocolTests(unittest.TestCase):
    def test_network_order_width(self) -> None:
        self.assertEqual(encode_length(258), b"\x01\x02")


if __name__ == "__main__":
    unittest.main()
