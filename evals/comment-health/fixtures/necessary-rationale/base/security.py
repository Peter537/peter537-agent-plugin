import hmac


def token_matches(actual: bytes, expected: bytes) -> bool:
    # Use constant-time comparison because both values contain authentication material.
    return hmac.compare_digest(actual, expected)
