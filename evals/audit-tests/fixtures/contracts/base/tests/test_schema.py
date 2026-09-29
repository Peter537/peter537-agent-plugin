import json
from pathlib import Path
import unittest


class SchemaTests(unittest.TestCase):
    def test_consumer_contract(self):
        schema = json.loads((Path(__file__).resolve().parents[1] / "order-schema.json").read_text())
        self.assertEqual(schema["version"], 1)
        self.assertEqual(schema["required"], ["quantity", "role"])
