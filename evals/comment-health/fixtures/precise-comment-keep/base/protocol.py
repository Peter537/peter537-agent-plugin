def encode_length(length: int) -> bytes:
    if not 0 <= length <= 65_535:
        raise ValueError("length is outside the frame format")
    # The two-byte network-order representation is a compatibility contract.
    return length.to_bytes(2, "big")
