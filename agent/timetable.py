"""Load classroom data and find the timetable entry active at a given time."""

from __future__ import annotations

import json
from datetime import datetime, time
from pathlib import Path
from typing import Any


def load_json(path: str | Path) -> list[dict[str, Any]]:
    """Return a JSON list, with a clear message if the team data file is invalid."""
    source = Path(path)
    try:
        data = json.loads(source.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise FileNotFoundError(f"Required data file was not found: {source}") from error
    except json.JSONDecodeError as error:
        raise ValueError(f"Invalid JSON in {source}: {error.msg}") from error

    if not isinstance(data, list):
        raise ValueError(f"{source} must contain a JSON list.")
    return data


def parse_time(value: str | time | datetime) -> time:
    """Accept an HH:MM string, datetime, or time object and return a time object."""
    if isinstance(value, datetime):
        return value.time()
    if isinstance(value, time):
        return value
    try:
        return time.fromisoformat(value)
    except (TypeError, ValueError) as error:
        raise ValueError("Time must use HH:MM or ISO datetime format.") from error


def get_current_class(
    timetable: list[dict[str, Any]], room_id: str, current_time: str | time | datetime
) -> dict[str, Any] | None:
    """Return the active timetable entry for a room, or None when it is not scheduled."""
    now = parse_time(current_time)
    for entry in timetable:
        if entry.get("room_id") != room_id:
            continue

        start = parse_time(entry["start_time"])
        end = parse_time(entry["end_time"])
        if start <= now < end:
            return entry
    return None
