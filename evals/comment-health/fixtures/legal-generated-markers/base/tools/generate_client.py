from pathlib import Path


def output_path() -> Path:
    """Return the generated artifact owned by this generator."""
    return Path("generated/client.py")
