from __future__ import annotations

import unittest
from pathlib import Path

from vision.occupancy_detector import SimulatedOccupancyDetector


PROJECT_ROOT = Path(__file__).resolve().parent.parent


class SimulatedDetectorTests(unittest.TestCase):
    def test_overcrowded_feed_has_five_messages(self) -> None:
        detector = SimulatedOccupancyDetector(PROJECT_ROOT / "data" / "demo_observations.json")
        observations = detector.get_observations("overcrowded")
        self.assertEqual(len(observations), 5)
        self.assertEqual(observations[-1]["room_id"], "CSE-201")
        self.assertEqual(observations[-1]["detected_students"], 56)


if __name__ == "__main__":
    unittest.main(verbosity=2)
