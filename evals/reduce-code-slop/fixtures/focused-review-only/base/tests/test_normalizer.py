import unittest

from accounts import account_key
from email import mailbox_key


class NormalizerTests(unittest.TestCase):
    def test_both_callers_share_normalization(self) -> None:
        self.assertEqual("account:alpha", account_key(" Alpha "))
        self.assertEqual("mailbox:team@example.invalid", mailbox_key(" TEAM@EXAMPLE.INVALID "))


if __name__ == "__main__":
    unittest.main()
