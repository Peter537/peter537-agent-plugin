_current_user: str | None = None


def begin_session(user: str) -> str:
    global _current_user
    if _current_user is None:
        _current_user = user
    return _current_user


def reset_session() -> None:
    global _current_user
    _current_user = None
