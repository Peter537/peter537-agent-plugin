"""Queue persistence contract."""

DATABASE_PATH = "state/queue.sqlite3"


def storage_kind() -> str:
    return "sqlite"
