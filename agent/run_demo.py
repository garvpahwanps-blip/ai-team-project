"""Run a short sample flow before the vision and dashboard modules are connected."""

from __future__ import annotations

import json

from .classroom_agent import ClassroomAgent


def main() -> None:
    agent = ClassroomAgent()
    for count in [52, 54, 55, 53, 56]:
        result = agent.evaluate_room(
            room_id="CSE-201",
            detected_students=count,
            confidence=0.91,
            timestamp="2026-10-27T10:30:00",
        )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
