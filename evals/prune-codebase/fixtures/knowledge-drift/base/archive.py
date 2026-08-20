ARCHIVE_CHUNK_SIZE = 50


def chunk(values: list[int]) -> list[int]:
    return values[:ARCHIVE_CHUNK_SIZE]
