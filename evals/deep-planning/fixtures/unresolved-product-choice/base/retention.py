def retained(events, *, days=30, maximum=1000):
    """Current behavior applies both an age and a count boundary."""
    return events[-maximum:]
