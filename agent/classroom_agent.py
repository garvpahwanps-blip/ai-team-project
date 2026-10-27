"""The model-based classroom monitoring agent used by the team dashboard."""

from __future__ import annotations

from collections import defaultdict, deque
from datetime import datetime
from pathlib import Path
from statistics import median
from typing import Any

from .database import ObservationStore
from .rules import determine_decision
from .timetable import get_current_class, load_json


class ClassroomAgent:
    """Evaluate room conditions using current and previous occupancy readings."""

    def __init__(
        self,
        data_directory: str | Path = "data",
        database_path: str | Path | None = "data/classroom.db",
        history_size: int = 5,
    ) -> None:
        if history_size < 1:
            raise ValueError("history_size must be at least 1.")

        data_directory = Path(data_directory)
        classroom_rows = load_json(data_directory / "classrooms.json")
        self.classrooms = {room["room_id"]: room for room in classroom_rows}
        self.timetable = load_json(data_directory / "timetable.json")
        self.history_size = history_size
        self.histories: dict[str, deque[int]] = defaultdict(
            lambda: deque(maxlen=self.history_size)
        )
        self.store = ObservationStore(database_path) if database_path else None

        if self.store:
            for room_id in self.classrooms:
                self.histories[room_id].extend(
                    self.store.recent_counts(room_id, self.history_size)
                )

    @staticmethod
    def _timestamp(value: str | datetime) -> tuple[str, datetime]:
        if isinstance(value, datetime):
            return value.isoformat(timespec="seconds"), value
        try:
            normalized = value.replace("Z", "+00:00")
            return value, datetime.fromisoformat(normalized)
        except (AttributeError, ValueError) as error:
            raise ValueError("timestamp must be an ISO value, such as 2026-10-27T10:30:00.") from error

    def evaluate_room(
        self,
        *,
        room_id: str,
        detected_students: int,
        confidence: float,
        timestamp: str | datetime,
    ) -> dict[str, Any]:
        """Record one reading and return the complete decision for the dashboard."""
        if room_id not in self.classrooms:
            raise ValueError(f"Unknown room_id: {room_id}")
        if not isinstance(detected_students, int) or detected_students < 0:
            raise ValueError("detected_students must be a non-negative integer.")
        if not 0 <= confidence <= 1:
            raise ValueError("confidence must be between 0 and 1.")

        timestamp_text, observed_at = self._timestamp(timestamp)
        room = self.classrooms[room_id]
        history = self.histories[room_id]
        history.append(detected_students)
        stable_occupancy = int(round(float(median(history))))

        if self.store:
            self.store.record_observation(room_id, detected_students, confidence, timestamp_text)

        active_class = get_current_class(self.timetable, room_id, observed_at)
        rule_result = determine_decision(
            room=room,
            active_class=active_class,
            stable_occupancy=stable_occupancy,
        )

        expected_students = int(active_class["expected_students"]) if active_class else None
        needs_alternative = rule_result["needs_alternative_room"]
        required_capacity = (
            max(stable_occupancy, expected_students or 0) if needs_alternative else None
        )

        decision = {
            "room_id": room_id,
            "detected_students": detected_students,
            "stable_occupancy": stable_occupancy,
            "confidence": confidence,
            "capacity": int(room["capacity"]),
            "timetable_status": "SCHEDULED" if active_class else "NOT_SCHEDULED",
            "course_name": active_class["course_name"] if active_class else None,
            "expected_students": expected_students,
            "classroom_state": rule_result["state"].value,
            "alert": rule_result["alert"],
            "needs_alternative_room": needs_alternative,
            "required_capacity": required_capacity,
            "required_room_type": (
                active_class["required_room_type"] if active_class else room["room_type"]
            ),
            "accessibility_required": bool(
                active_class.get("accessibility_required", False) if active_class else False
            ),
            "timestamp": timestamp_text,
        }

        if self.store:
            self.store.record_status(decision)
        return decision
