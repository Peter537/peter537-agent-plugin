"""Formatting used by the synthetic status page."""


def format_message(title: str, body: str) -> str:
    """Render the only supported status-message format."""
    clean_title = title.strip()
    clean_body = body.strip()
    if not clean_title or not clean_body:
        raise ValueError("title and body are required")
    return f"{clean_title}: {clean_body}"
