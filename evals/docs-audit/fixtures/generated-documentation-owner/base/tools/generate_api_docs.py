"""Generate the owned API reference without external dependencies."""

from pathlib import Path


def render() -> str:
    return "<!-- GENERATED: edit tools/generate_api_docs.py -->\n# API\n\nUse `GET /health`.\n"


def main() -> None:
    Path("docs/api.md").write_text(render(), encoding="utf-8")


if __name__ == "__main__":
    main()
