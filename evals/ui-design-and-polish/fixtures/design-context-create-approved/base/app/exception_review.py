VALID_STATES = ("release", "hold", "quarantine")


def ordered_evidence(readings):
    return tuple(sorted(readings, key=lambda item: item["recorded_at"]))


def can_commit(state, confirmed):
    if state not in VALID_STATES:
        return False
    return state != "quarantine" or confirmed
