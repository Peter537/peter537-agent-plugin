def search(connection, text):
    if not text:
        return []
    pattern = text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return connection.execute(
        "SELECT name FROM records WHERE name LIKE ? ESCAPE '\\\\' ORDER BY name",
        ("%" + pattern + "%",),
    ).fetchall()
