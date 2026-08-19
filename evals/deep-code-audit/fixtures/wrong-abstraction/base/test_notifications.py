import unittest

from notifications import InvalidRecipient, prepare_notification


class NotificationTests(unittest.TestCase):
    def test_email_validation_raises(self) -> None:
        with self.assertRaises(InvalidRecipient):
            prepare_notification("invalid", "Ready", "email")

    def test_sms_validation_returns_rejection(self) -> None:
        result = prepare_notification("invalid", "Ready", "sms")
        self.assertFalse(result.accepted)

    def test_channel_specific_options(self) -> None:
        email = prepare_notification(
            "reader@example.invalid",
            "Ready",
            "email",
            require_receipt=True,
        )
        sms = prepare_notification("+4512345678", "Ready", "sms", urgent=True)
        self.assertTrue(email.receipt_requested)
        self.assertTrue(sms.body.startswith("URGENT: "))


if __name__ == "__main__":
    unittest.main()
