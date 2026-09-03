import unittest

from uploader import MAX_REQUEST_SIZE, plan_requests


class PlanRequestsTests(unittest.TestCase):
    def test_requests_respect_limit_and_order(self) -> None:
        record_ids = [f"record-{index}" for index in range(165)]

        requests = plan_requests(record_ids)

        self.assertTrue(all(len(request) <= MAX_REQUEST_SIZE for request in requests))
        self.assertEqual(record_ids, [record_id for request in requests for record_id in request])

    def test_invalid_id_rejects_the_complete_job(self) -> None:
        with self.assertRaises(ValueError):
            plan_requests(["record-1", " ", "record-3"])


if __name__ == "__main__":
    unittest.main()
