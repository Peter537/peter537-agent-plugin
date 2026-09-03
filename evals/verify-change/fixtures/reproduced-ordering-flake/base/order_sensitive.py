def process(sequence: list[str]) -> list[str]:
    state: list[str] = []
    for item in sequence:
        if item == "reset":
            continue
        state.append(item)
    return state
