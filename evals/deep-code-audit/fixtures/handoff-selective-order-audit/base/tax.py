"""Independent synthetic tax calculation with a documented rounding contract."""


def tax_cents(amount_cents: int, rate_basis_points: int) -> int:
    if amount_cents < 0 or rate_basis_points < 0:
        raise ValueError("amount and rate must be non-negative")
    return amount_cents * rate_basis_points // 10_000
