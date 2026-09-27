def export_rows(rows):
    return "\n".join(",".join(map(str, row)) for row in rows)
