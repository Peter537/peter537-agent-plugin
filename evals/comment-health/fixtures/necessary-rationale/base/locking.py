from threading import Lock


_accounts_lock = Lock()
_ledger_lock = Lock()


def settle() -> None:
    # Acquire accounts before ledger everywhere to prevent an AB/BA deadlock.
    with _accounts_lock:
        with _ledger_lock:
            return None
