from normalizer import normalize_identifier


def mailbox_key(address: str) -> str:
    return "mailbox:" + normalize_identifier(address)
