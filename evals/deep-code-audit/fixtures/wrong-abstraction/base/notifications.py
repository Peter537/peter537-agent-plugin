"""Intentionally mixed notification policies for audit evaluation."""

from dataclasses import dataclass


class InvalidRecipient(ValueError):
    pass


@dataclass(frozen=True)
class PreparedNotification:
    accepted: bool
    destination: str
    body: str
    receipt_requested: bool = False


def prepare_notification(
    recipient: str,
    body: str,
    mode: str,
    *,
    urgent: bool = False,
    require_receipt: bool = False,
) -> PreparedNotification:
    if mode == "email":
        if "@" not in recipient:
            raise InvalidRecipient("email recipient is invalid")
        subject = "URGENT: notification" if urgent else "Notification"
        return PreparedNotification(
            accepted=True,
            destination=recipient,
            body=f"{subject}\n\n{body}",
            receipt_requested=require_receipt,
        )

    if mode == "sms":
        if not recipient.startswith("+") or not recipient[1:].isdigit():
            return PreparedNotification(False, recipient, body)
        prefix = "URGENT: " if urgent else ""
        return PreparedNotification(True, recipient, (prefix + body)[:160])

    raise ValueError(f"unsupported notification mode: {mode}")
