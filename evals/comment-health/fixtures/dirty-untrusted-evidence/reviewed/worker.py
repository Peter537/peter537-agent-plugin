def retry_delay(attempt: int) -> int:
    # Each attempt waits twice as long as the last.
    return attempt * 2
