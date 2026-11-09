"""Read the latest occupancy status sent by classroom monitoring feeds."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_live_room_status(data_directory: str | Path = "data") -> dict[str, dict[str, Any]]:
    """Return the latest status for every room from the shared campus status feed."""
    source = Path(data_directory) / "live_room_status.json"
    if not source.is_file():
        return {}

    raw_statuses = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(raw_statuses, dict):
        raise ValueError("live_room_status.json must contain a room-ID object.")

    statuses: dict[str, dict[str, Any]] = {}
    for room_id, status in raw_statuses.items():
        if not isinstance(status, dict):
            raise ValueError(f"Live status for {room_id} must be an object.")
        occupancy = status.get("current_occupancy", 0)
        if not isinstance(occupancy, int) or occupancy < 0:
            raise ValueError(f"Live occupancy for {room_id} must be a non-negative integer.")
        statuses[str(room_id)] = {
            "current_occupancy": occupancy,
            "state": str(status.get("state", "UNKNOWN")),
            "last_updated": str(status.get("last_updated", "Not reported")),
        }
    return statuses
