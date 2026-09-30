def _key(principal, item, units):
    if principal is None:
        raise PermissionError("Sign in required")
    if type(units) is not int or units <= 0:
        raise ValueError("Positive units required")
    return principal["tenant"], item


def reserve(principal, item, units, operation_id, stock, receipts):
    key = _key(principal, item, units)
    if stock[key] < units:
        raise ValueError("Insufficient stock")
    stock[key] -= units
    return stock[key]


def release(principal, item, units, operation_id, stock, receipts):
    key = _key(principal, item, units)
    receipt_key = principal["tenant"], principal["subject"], "release", operation_id
    payload = item, units
    if receipt_key in receipts:
        previous_payload, previous_result = receipts[receipt_key]
        if payload != previous_payload:
            raise ValueError("Operation ID reused with different payload")
        return previous_result
    stock[key] += units
    receipts[receipt_key] = payload, stock[key]
    return stock[key]
