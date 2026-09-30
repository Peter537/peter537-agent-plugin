"""Observe storage calls in memory; no actual uploaded files are written."""
import unittest
from pathlib import Path
from unittest.mock import patch

from web import upload


class UploadByteBoundaryTests(unittest.TestCase):
    def test_actual_bytes_reach_storage_at_and_over_contract_limit(self):
        for size in [64, 65]:
            with self.subTest(size=size):
                calls = []
                def observe_write(path, data):
                    calls.append((path, bytes(data)))
                    return len(data)
                with patch.object(Path, "write_bytes", observe_write):
                    upload("sample.bin", b"x" * size)
                self.assertEqual(calls, [(Path("uploads/sample.bin"), b"x" * size)])


if __name__ == "__main__":
    unittest.main()
