class RecordError(ValueError):
    def __init__(self) -> None:
        self.code = "invalid-record"
        super().__init__(self.code)


def parse_record(value: str) -> tuple[str, int]:
    parts = value.split(":")
    if len(parts) != 2 or not parts[0] or not parts[1].isdigit():
        raise RecordError()
    return parts[0], int(parts[1])
