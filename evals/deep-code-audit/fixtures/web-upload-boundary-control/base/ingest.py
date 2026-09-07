MAX_BYTES = 1024


def receive_upload(data, store):
    if len(data) > MAX_BYTES:
        raise ValueError("Upload exceeds size limit")
    return _store_upload(data, store)


def _store_upload(data, store):
    return store(data)
