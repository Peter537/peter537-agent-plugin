import unittest

from ingest import MAX_BYTES, receive_upload


class UploadBoundaryTests(unittest.TestCase):
    def test_limit_accepts_exact_boundary(self):
        stored = []
        receive_upload(b"x" * MAX_BYTES, stored.append)
        self.assertEqual(len(stored), 1)
        self.assertEqual(len(stored[0]), MAX_BYTES)

    def test_oversized_body_never_reaches_storage(self):
        stored = []
        with self.assertRaises(ValueError):
            receive_upload(b"x" * (MAX_BYTES + 1), stored.append)
        self.assertEqual(stored, [])


if __name__ == "__main__":
    unittest.main()
