from decimal import Decimal


def tax_total(net: Decimal, rate: Decimal) -> Decimal:
    return round(float(net * rate), 2)
