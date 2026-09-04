from review_api import reject_record


def main() -> int:
    assert reject_record("synthetic-17") == {
        "id": "synthetic-17",
        "state": "rejected",
    }
    try:
        reject_record(" ")
    except ValueError:
        return 0
    raise AssertionError("blank identifiers must be rejected")


if __name__ == "__main__":
    raise SystemExit(main())

