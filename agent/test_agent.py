"""Tests for the agreed classroom states and the agent's observation memory."""

from __future__ import annotations

import unittest
from pathlib import Path

from agent.classroom_agent import ClassroomAgent


PROJECT_ROOT = Path(__file__).resolve().parent.parent


class ClassroomAgentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.agent = ClassroomAgent(
            data_directory=PROJECT_ROOT / "data", database_path=None
        )

    def test_overcrowded_room_requests_alternative(self) -> None:
        result = self.agent.evaluate_room(
            room_id="CSE-201",
            detected_students=55,
            confidence=0.91,
            timestamp="2026-10-27T10:30:00",
        )
        self.assertEqual(result["classroom_state"], "OVER_CROWDED")
        self.assertTrue(result["needs_alternative_room"])
        self.assertEqual(result["required_capacity"], 55)

    def test_scheduled_active_class(self) -> None:
        result = self.agent.evaluate_room(
            room_id="CSE-201",
            detected_students=30,
            confidence=0.95,
            timestamp="2026-10-27T10:30:00",
        )
        self.assertEqual(result["classroom_state"], "SCHEDULED_ACTIVE")

    def test_unscheduled_usage(self) -> None:
        result = self.agent.evaluate_room(
            room_id="CSE-201",
            detected_students=15,
            confidence=0.90,
            timestamp="2026-10-27T14:00:00",
        )
        self.assertEqual(result["classroom_state"], "UNSCHEDULED_USAGE")

    def test_empty_room(self) -> None:
        result = self.agent.evaluate_room(
            room_id="CSE-201",
            detected_students=0,
            confidence=0.99,
            timestamp="2026-10-27T14:00:00",
        )
        self.assertEqual(result["classroom_state"], "EMPTY")

    def test_unavailable_scheduled_room(self) -> None:
        self.agent.classrooms["LAB-101"]["available"] = False
        result = self.agent.evaluate_room(
            room_id="LAB-101",
            detected_students=0,
            confidence=0.99,
            timestamp="2026-10-27T11:30:00",
        )
        self.assertEqual(result["classroom_state"], "UNAVAILABLE")
        self.assertTrue(result["needs_alternative_room"])
        self.assertEqual(result["required_room_type"], "LAB")

    def test_uses_median_of_five_observations(self) -> None:
        for count in [10, 12, 13, 15, 80]:
            result = self.agent.evaluate_room(
                room_id="CSE-201",
                detected_students=count,
                confidence=0.90,
                timestamp="2026-10-27T10:30:00",
            )
        self.assertEqual(result["stable_occupancy"], 13)
        self.assertEqual(result["classroom_state"], "UNDERUTILIZED")


if __name__ == "__main__":
    unittest.main(verbosity=2)
