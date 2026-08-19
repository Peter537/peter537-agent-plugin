from normalizer import normalize_identifier


def account_key(name: str) -> str:
    return "account:" + normalize_identifier(name)
