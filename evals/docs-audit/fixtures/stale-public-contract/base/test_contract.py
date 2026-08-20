import json
import unittest
from pathlib import Path

import app


class ContractTests(unittest.TestCase):
    def test_public_contract(self) -> None:
        settings = json.loads(Path("settings.json").read_text(encoding="utf-8"))
        self.assertEqual(app.ROUTE, "/v2/items")
        self.assertEqual(settings["port"], 9000)
        self.assertEqual(app.response(), {"items": [{"title": "Example"}]})


if __name__ == "__main__":
    unittest.main()
