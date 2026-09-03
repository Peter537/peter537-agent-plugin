from __future__ import annotations

import json
import unittest
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ContractParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.test_ids: set[str] = set()
        self.states: set[str] = set()
        self.state_links: set[str] = set()
        self.stylesheets: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if values.get("data-testid"):
            self.test_ids.add(values["data-testid"] or "")
        if values.get("data-state-panel"):
            self.states.add(values["data-state-panel"] or "")
        if values.get("data-state-link"):
            self.state_links.add(values["data-state-link"] or "")
        if tag == "link" and values.get("rel") == "stylesheet" and values.get("href"):
            self.stylesheets.add(values["href"] or "")


class ProtectedContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.css = (ROOT / "styles.css").read_text(encoding="utf-8")
        self.javascript = (ROOT / "app.js").read_text(encoding="utf-8")
        self.parser = ContractParser()
        self.parser.feed(self.html)

    def test_stable_hooks_and_states_remain(self) -> None:
        self.assertTrue(
            {
                "state-controls",
                "state-populated",
                "state-empty",
                "state-error",
                "state-permission",
                "sensor-provenance",
                "open-source",
                "quarantine",
                "quarantine-dialog",
                "cancel-quarantine",
                "confirm-quarantine",
                "long-reason",
            }.issubset(self.parser.test_ids)
        )
        self.assertEqual({"populated", "empty", "error", "permission"}, self.parser.states)
        self.assertEqual(self.parser.states, self.parser.state_links)

    def test_canonical_stylesheets_remain_connected(self) -> None:
        self.assertTrue(
            {"styles/tokens.css", "styles/components.css", "styles.css"}.issubset(
                self.parser.stylesheets
            )
        )
        self.assertIn("status-chip", self.html)
        self.assertIn("action-button--destructive", self.html)
        self.assertIn("sensor-provenance", self.html)

    def test_localized_and_destructive_contracts_remain(self) -> None:
        self.assertIn("Gentagne temperaturudsving efter omlæsning", self.html)
        self.assertIn("Sæt CC-1842 i karantæne?", self.html)
        self.assertIn('event.key.toLowerCase() === "q"', self.javascript)
        self.assertIn("dialog.showModal()", self.javascript)
        self.assertIn('setAttribute("aria-current", "page")', self.javascript)

    def test_exemplar_and_stale_concept_are_not_copied(self) -> None:
        target = f"{self.html}\n{self.css}".casefold()
        for forbidden in ("aurora-board", "coastal review board", "#8b5cf6", "aurora-ui"):
            self.assertNotIn(forbidden, target)

    def test_exemplar_metadata_is_bounded(self) -> None:
        payload = json.loads((ROOT / "design" / "exemplars.json").read_text(encoding="utf-8"))
        self.assertEqual(1, payload.get("schemaVersion"))
        self.assertEqual(1, len(payload.get("entries", [])))
        exemplar = payload["entries"][0]
        for field in ("purpose", "applicability", "nonCopyGuidance", "source", "license"):
            self.assertTrue(exemplar.get(field))
        source = Path(exemplar["source"]["path"])
        self.assertFalse(source.is_absolute())
        self.assertNotIn("..", source.parts)
        self.assertTrue((ROOT / source).is_file())


if __name__ == "__main__":
    unittest.main()
