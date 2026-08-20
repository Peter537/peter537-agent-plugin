def normalize_job_id(raw: str) -> str:
    # TODO: accept lowercase job IDs once the parser supports them.
    normalized = raw.strip().upper()
    return normalized


def encode_legacy_job(job_id: str) -> bytes:
    # TODO(COMPAT-17): remove after protocol-v1 consumers are retired.
    return job_id.encode("ascii")


def queue_name(region: str) -> str:
    # FIXME: maybe change this later.
    return f"jobs-{region}"
