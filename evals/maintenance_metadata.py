"""Private parsers shared by repository-maintenance checks.

This module deliberately implements only the bounded mapping/scalar YAML
subset used by the repository's skill metadata. It is not a general YAML
parser and rejects unsupported syntax instead of guessing.
"""

from __future__ import annotations

import json
import re


__all__ = ["BoundedYamlParseError", "parse_bounded_yaml"]


_YAML_KEY = re.compile(r"^[A-Za-z_][A-Za-z0-9_-]*$")
_PLAIN_YAML_NUMBER = re.compile(
    r"[-+]?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][-+]?[0-9]+)?$"
)


class BoundedYamlParseError(ValueError):
    """Repository metadata is outside the supported YAML subset."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def _parse_yaml_scalar(raw: str) -> object:
    value = raw.strip()
    if not value:
        raise BoundedYamlParseError("empty-yaml-scalar")
    if value.startswith('"'):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError as error:
            raise BoundedYamlParseError("yaml-string") from error
        if not isinstance(parsed, str):
            raise BoundedYamlParseError("yaml-scalar")
        return parsed
    if value.startswith("'"):
        if len(value) < 2 or not value.endswith("'"):
            raise BoundedYamlParseError("yaml-string")
        return value[1:-1].replace("''", "'")
    value = re.split(r"[ \t]+#", value, maxsplit=1)[0].rstrip()
    if _PLAIN_YAML_NUMBER.fullmatch(value):
        return float(value) if any(character in value for character in ".eE") else int(value)
    if not value or value[0] in "-?:,[]{}#&*!|>@`\"'":
        raise BoundedYamlParseError("unsupported-yaml")
    if re.search(r":[ \t]", value):
        raise BoundedYamlParseError("unsupported-yaml")
    lowered = value.casefold()
    if lowered in {"true", "false"}:
        return lowered == "true"
    if lowered in {"null", "~"}:
        return None
    return value


def parse_bounded_yaml(text: str) -> dict[str, object]:
    """Parse the mapping/scalar YAML subset used by repository metadata."""

    if len(text.encode("utf-8")) > 1024 * 1024:
        raise BoundedYamlParseError("yaml-size")
    root: dict[str, object] = {}
    stack: list[tuple[int, dict[str, object]]] = [(-2, root)]
    created_maps: list[dict[str, object]] = []
    for raw_line in text.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        if "\t" in raw_line[: len(raw_line) - len(raw_line.lstrip())]:
            raise BoundedYamlParseError("yaml-tab")
        indentation = len(raw_line) - len(raw_line.lstrip(" "))
        if indentation % 2:
            raise BoundedYamlParseError("yaml-indentation")
        line = raw_line[indentation:]
        if line.startswith(("---", "...", "- ")) or ":" not in line:
            raise BoundedYamlParseError("unsupported-yaml")
        key, raw_value = line.split(":", 1)
        if not _YAML_KEY.fullmatch(key):
            raise BoundedYamlParseError("yaml-key")

        while stack and indentation <= stack[-1][0]:
            stack.pop()
        if not stack or indentation != stack[-1][0] + 2:
            raise BoundedYamlParseError("yaml-indentation")
        current = stack[-1][1]
        if key in current:
            raise BoundedYamlParseError("yaml-duplicate-key")
        if not raw_value.strip():
            child: dict[str, object] = {}
            current[key] = child
            stack.append((indentation, child))
            created_maps.append(child)
        else:
            current[key] = _parse_yaml_scalar(raw_value)
    if not root:
        raise BoundedYamlParseError("empty-yaml")
    if any(not mapping for mapping in created_maps):
        raise BoundedYamlParseError("empty-yaml-mapping")
    return root
