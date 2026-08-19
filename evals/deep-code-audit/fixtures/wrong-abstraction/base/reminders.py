"""Caller that must understand notification mode-specific flags."""

from notifications import PreparedNotification, prepare_notification


def prepare_reminder(recipient: str, message: str, prefers_sms: bool) -> PreparedNotification:
    mode = "sms" if prefers_sms else "email"
    return prepare_notification(
        recipient,
        message,
        mode,
        urgent=prefers_sms,
        require_receipt=not prefers_sms,
    )
