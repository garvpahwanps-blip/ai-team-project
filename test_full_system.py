from __future__ import annotations

import unittest
from pathlib import Path

from monitoring_system import ClassroomMonitoringSystem


PROJECT_ROOT = Path(__file__).resolve().parent


class FullSystemTests(unittest.TestCase):
    def test_overcrowded_scenario_gets_an_alternative_room(self) -> None:
        system = ClassroomMonitoringSystem(PROJECT_ROOT / "data", database_path=None)
        result = system.process_scenario("overcrowded")
        self.assertEqual(result["decision"]["classroom_state"], "OVER_CROWDED")
        self.assertEqual(result["recommendation"]["recommended_room_id"], "CSE-305")

    def test_unscheduled_scenario_does_not_relocate_students(self) -> None:
        system = ClassroomMonitoringSystem(PROJECT_ROOT / "data", database_path=None)
        result = system.process_scenario("unscheduled_usage")
        self.assertEqual(result["decision"]["classroom_state"], "UNSCHEDULED_USAGE")
        self.assertIsNone(result["recommendation"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
