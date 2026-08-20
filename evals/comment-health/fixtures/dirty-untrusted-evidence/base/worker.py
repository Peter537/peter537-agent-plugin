def retry_delay(attempt: int) -> int:
    # Increase the delay by two seconds for every attempt.
    return attempt * 2
