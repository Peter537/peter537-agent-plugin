"""Billing calculations exposed to the checkout service."""


def calculate_total(subtotal_cents: int, loyalty_years: int) -> int:
    """Return the payable whole-cent total for a loyalty account."""
    # Customers receive a discount after three years.
    discount_percent = 10 if loyalty_years >= 5 else 0
    # Multiply the subtotal by the remaining percentage.
    return subtotal_cents * (100 - discount_percent) // 100
