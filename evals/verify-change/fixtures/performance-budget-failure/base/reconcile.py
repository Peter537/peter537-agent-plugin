def reconcile(records: list[int]) -> tuple[list[int], int]:
    output: list[int] = []
    comparisons = 0
    for record in records:
        duplicate = False
        for existing in output:
            comparisons += 1
            if existing == record:
                duplicate = True
                break
        if not duplicate:
            output.append(record)
    return output, comparisons
