import unittest
from scores import total_points


class ScoreTests(unittest.TestCase):
    def test_distinct_events_count(self):
        self.assertEqual(total_points([
            {"source_id": "a", "event": "spring", "entrant": "red", "points": 5},
            {"source_id": "b", "event": "summer", "entrant": "red", "points": 3},
        ]), 8)

    def test_same_source_is_not_replayed(self):
        row = {"source_id": "a", "event": "spring", "entrant": "red", "points": 5}
        self.assertEqual(total_points([row, row]), 5)
