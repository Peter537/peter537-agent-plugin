import unittest

from payload import Settings, decode_settings


class PayloadTests(unittest.TestCase):
    def test_decodes_supported_shape(self) -> None:
        self.assertEqual(Settings("eu-west", 3), decode_settings('{"region":" eu-west ","retries":3}'))

    def test_rejects_missing_member(self) -> None:
        with self.assertRaises(ValueError):
            decode_settings('{"region":"eu-west"}')

    def test_rejects_non_object(self) -> None:
        with self.assertRaises((TypeError, ValueError)):
            decode_settings('[]')


if __name__ == "__main__":
    unittest.main()
