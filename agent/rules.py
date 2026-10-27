"""Decision rules for the intelligent classroom agent."""

from __future__ import annotations

from enum import Enum
from typing import Any


class ClassroomState(str, Enum):
    EMPTY = "EMPTY"
    SCHEDULED_ACTIVE = "SCHEDULED_ACTIVE"
    UNSCHEDULED_USAGE = "UNSCHEDULED_USAGE"
    UNDERUTILIZED = "UNDERUTILIZED"
    OVER_CROWDED = "OVER_CROWDED"
    UNAVAILABLE = "UNAVAILABLE"


def determine_decision(
    *, room: dict[str, Any], active_class: dict[str, Any] | None, stable_occupancy: int
) -> dict[str, Any]:
    """Apply the team-agreed rules and return a state, alert, and relocation need."""
    capacity = int(room["capacity"])
    is_scheduled = active_class is not None
    expected_students = int(active_class["expected_students"]) if active_class else 0

    # A scheduled room made unavailable by facilities must be replaced even if
    # the camera currently sees no students.
    if is_scheduled and not room.get("available", True):
        return {
            "state": ClassroomState.UNAVAILABLE,
            "alert": "A class is scheduled, but this classroom is unavailable.",
            "needs_alternative_room": True,
        }

    if stable_occupancy > capacity:
        return {
            "state": ClassroomState.OVER_CROWDED,
            "alert": f"Room capacity exceeded by {stable_occupancy - capacity} students.",
            "needs_alternative_room": True,
        }

    # A value of 1 or 2 is treated as detection noise or staff movement.
    if not is_scheduled and stable_occupancy > 2:
        return {
            "state": ClassroomState.UNSCHEDULED_USAGE,
            "alert": "Students are present even though no class is scheduled.",
            "needs_alternative_room": False,
        }

    if not is_scheduled:
        return {
            "state": ClassroomState.EMPTY,
            "alert": "Room is empty and available.",
            "needs_alternative_room": False,
        }

    if expected_students and stable_occupancy < expected_students * 0.5:
        return {
            "state": ClassroomState.UNDERUTILIZED,
            "alert": "Attendance is below 50% of the expected class size.",
            "needs_alternative_room": False,
        }

    return {
        "state": ClassroomState.SCHEDULED_ACTIVE,
        "alert": "Scheduled class is operating within room capacity.",
        "needs_alternative_room": False,
    }
