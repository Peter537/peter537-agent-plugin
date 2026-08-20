import unittest

import retention


class RetentionContractTests(unittest.TestCase):
    def test_product_retention_policy(self) -> None:
        self.assertEqual(retention.RETENTION_DAYS, 60)


if __name__ == "__main__":
    unittest.main()
