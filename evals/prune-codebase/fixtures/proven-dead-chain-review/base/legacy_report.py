def legacy_report(rows: list[int]) -> str:
    return _render_legacy(_legacy_total(rows))


def _legacy_total(rows: list[int]) -> int:
    return sum(rows)


def _render_legacy(total: int) -> str:
    return f"Legacy total: {total}"
