def adapt(record, *, audit=False):
    result = {"id": record["legacy_id"], "name": record["display_name"]}
    if audit:
        result["legacy_trace"] = record.get("trace")
    result["unused_marker"] = True
    return result
