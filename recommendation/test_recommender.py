from __future__ import annotations

import unittest
from pathlib import Path

from recommendation.room_recommender import RoomRecommender


PROJECT_ROOT = Path(__file__).resolve().parent.parent


class RoomRecommenderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.recommender = RoomRecommender(PROJECT_ROOT / "data")
        self.request = {
            "source_room_id": "CSE-201",
            "required_capacity": 54,
            "required_room_type": "CLASSROOM",
            "accessibility_required": False,
            "timestamp": "2026-10-27T10:30:00",
        }

    def test_finds_nearest_suitable_room(self) -> None:
        result = self.recommender.recommend(self.request)
        self.assertTrue(result["alternative_found"])
        self.assertEqual(result["recommended_room_id"], "CSE-305")
        self.assertGreater(result["distance_meters"], 0)

    def test_rejects_room_when_someone_is_already_inside(self) -> None:
        result = self.recommender.recommend(self.request, {"CSE-305": 3})
        self.assertFalse(result["alternative_found"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
