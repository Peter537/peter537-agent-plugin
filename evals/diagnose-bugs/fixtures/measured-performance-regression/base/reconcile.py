def reconcile(expected: list[str], actual: list[str]) -> tuple[list[str], int]:
    missing: list[str] = []
    comparisons = 0
    for item in expected:
        found = False
        for candidate in actual:
            comparisons += 1
            if candidate == item:
                found = True
        if not found:
            missing.append(item)
    return missing, comparisons
