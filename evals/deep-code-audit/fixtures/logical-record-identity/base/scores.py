def total_points(records):
    seen_sources = set()
    total = 0
    for record in records:
        if record["source_id"] not in seen_sources:
            total += record["points"]
            seen_sources.add(record["source_id"])
    return total
