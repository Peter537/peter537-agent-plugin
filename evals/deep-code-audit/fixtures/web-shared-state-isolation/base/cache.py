def _owned_record(principal, document_id, records):
    if principal is None:
        raise PermissionError("Sign in required")
    record = records[(principal["tenant"], document_id)]
    if record["owner"] != principal["subject"]:
        raise PermissionError("Owner required")
    return record


def read_document(principal, document_id, records, cache):
    if principal is None:
        raise PermissionError("Sign in required")
    if document_id in cache:
        return cache[document_id]
    record = _owned_record(principal, document_id, records)
    cache[document_id] = record["body"]
    return record["body"]


def read_summary(principal, document_id, records, cache):
    record = _owned_record(principal, document_id, records)
    key = principal["tenant"], principal["subject"], document_id
    if key not in cache:
        cache[key] = record["summary"]
    return cache[key]


def public_labels():
    return ("draft", "published")
