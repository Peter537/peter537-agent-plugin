import unittest

from batching import build_batches


class BuildBatchesTests(unittest.TestCase):
    def test_default_batching_preserves_order(self) -> None:
        record_ids = [f"record-{index}" for index in range(205)]

        batches = build_batches(record_ids)

        self.assertEqual([100, 100, 5], [len(batch) for batch in batches])
        self.assertEqual(record_ids, [record_id for batch in batches for record_id in batch])

    def test_batch_size_is_configurable(self) -> None:
        self.assertEqual([["a", "b"], ["c"]], build_batches(["a", "b", "c"], batch_size=2))

    def test_all_ids_are_validated_before_batching(self) -> None:
        with self.assertRaises(ValueError):
            build_batches(["valid", " ", "also-valid"], batch_size=1)

    def test_jobs_above_approved_capacity_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            build_batches([f"record-{index}" for index in range(251)])


if __name__ == "__main__":
    unittest.main()
