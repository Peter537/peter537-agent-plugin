NEW_CHECKOUT_COMPLETE = True


def checkout_total(values: list[int]) -> int:
    if NEW_CHECKOUT_COMPLETE:
        return sum(values)
    return legacy_checkout_total(values)


def legacy_checkout_total(values: list[int]) -> int:
    return sum(values)
