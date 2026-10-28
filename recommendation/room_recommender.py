"""Filter alternative classrooms, then select the nearest using A* search."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agent.timetable import get_current_class

from .campus_graph import CampusGraph


class RoomRecommender:
    def __init__(self, data_directory: str | Path = "data") -> None:
        directory = Path(data_directory)
        self.rooms: list[dict[str, Any]] = json.loads(
            (directory / "classrooms.json").read_text(encoding="utf-8")
        )
        self.timetable: list[dict[str, Any]] = json.loads(
            (directory / "timetable.json").read_text(encoding="utf-8")
        )
        self.graph = CampusGraph(directory / "campus_graph.json")

    def _candidate_rooms(
        self,
        request: dict[str, Any],
        current_occupancies: dict[str, int],
    ) -> list[dict[str, Any]]:
        candidates: list[dict[str, Any]] = []
        for room in self.rooms:
            room_id = room["room_id"]
            if room_id == request["source_room_id"]:
                continue
            if not room.get("available", True):
                continue
            if room["room_type"] != request["required_room_type"]:
                continue
            if request.get("accessibility_required", False) and not room.get("accessibility", False):
                continue
            if get_current_class(self.timetable, room_id, request["timestamp"]):
                continue

            current_occupancy = int(current_occupancies.get(room_id, 0))
            free_seats = int(room["capacity"]) - current_occupancy
            if current_occupancy > 0 or free_seats < int(request["required_capacity"]):
                continue
            candidates.append(room)
        return candidates

    def recommend(
        self,
        request: dict[str, Any],
        current_occupancies: dict[str, int] | None = None,
    ) -> dict[str, Any]:
        """Return the nearest room satisfying availability and teaching constraints."""
        current_occupancies = current_occupancies or {}
        routes: list[tuple[int, dict[str, Any], list[str]]] = []
        for room in self._candidate_rooms(request, current_occupancies):
            result = self.graph.find_route(request["source_room_id"], room["room_id"])
            if result is not None:
                route, distance = result
                routes.append((distance, room, route))

        if not routes:
            return {
                "source_room_id": request["source_room_id"],
                "alternative_found": False,
                "recommended_room_id": None,
                "message": "No suitable available classroom was found.",
                "route": [],
                "distance_meters": None,
            }

        distance, room, route = min(routes, key=lambda item: (item[0], item[1]["room_id"]))
        return {
            "source_room_id": request["source_room_id"],
            "alternative_found": True,
            "recommended_room_id": room["room_id"],
            "recommended_room_name": room["room_name"],
            "recommended_room_capacity": room["capacity"],
            "distance_meters": distance,
            "route": route,
            "message": f"{room['room_id']} is the nearest suitable available classroom.",
        }
