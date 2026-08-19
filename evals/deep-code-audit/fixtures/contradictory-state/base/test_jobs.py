import unittest

from jobs import Job


class JobTests(unittest.TestCase):
    def test_successful_lifecycle(self) -> None:
        job = Job()
        job.start()
        self.assertTrue(job.is_running)

        job.complete()
        self.assertFalse(job.is_running)
        self.assertTrue(job.is_complete)

    def test_failed_lifecycle(self) -> None:
        job = Job()
        job.start()
        job.fail()
        self.assertFalse(job.is_running)
        self.assertTrue(job.has_failed)


if __name__ == "__main__":
    unittest.main()
