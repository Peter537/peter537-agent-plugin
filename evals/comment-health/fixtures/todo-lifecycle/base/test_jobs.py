import unittest

from jobs import normalize_job_id


class JobTests(unittest.TestCase):
    def test_lowercase_ids_are_accepted(self) -> None:
        self.assertEqual(normalize_job_id(" job-4 "), "JOB-4")


if __name__ == "__main__":
    unittest.main()
