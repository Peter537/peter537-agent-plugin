# Synthetic notification rules

Email recipients must contain `@`; invalid email addresses raise `InvalidRecipient`. Email can request a delivery receipt.

SMS recipients must use E.164-like `+` and digits; invalid SMS recipients return a rejected result. SMS can mark a message urgent but does not support receipts.
