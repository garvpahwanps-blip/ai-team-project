"""Weighted campus graph and A* route finder."""

from __future__ import annotations

import heapq
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any


class CampusGraph:
    def __init__(self, graph_path: str | Path = "data/campus_graph.json") -> None:
        source = Path(graph_path)
        data: dict[str, Any] = json.loads(source.read_text(encoding="utf-8"))
        self.nodes: dict[str, dict[str, Any]] = data["nodes"]
        self.adjacency: dict[str, list[tuple[str, float]]] = defaultdict(list)
        for edge in data["edges"]:
            start, end = edge["from"], edge["to"]
            distance = float(edge["distance_meters"])
            self.adjacency[start].append((end, distance))
            self.adjacency[end].append((start, distance))

    def _heuristic(self, start: str, destination: str) -> float:
        """Straight-line estimate used by A*; coordinates are in campus-map metres."""
        x1, y1 = self.nodes[start]["coordinates"]
        x2, y2 = self.nodes[destination]["coordinates"]
        return math.hypot(x2 - x1, y2 - y1)

    def find_route(self, start: str, destination: str) -> tuple[list[str], int] | None:
        """Return the lowest-distance path and its distance in metres."""
        if start not in self.nodes or destination not in self.nodes:
            raise ValueError("Both source and destination must be valid campus graph nodes.")

        frontier: list[tuple[float, float, str, list[str]]] = [
            (self._heuristic(start, destination), 0.0, start, [start])
        ]
        best_cost: dict[str, float] = {start: 0.0}

        while frontier:
            _, cost, current, path = heapq.heappop(frontier)
            if current == destination:
                return path, int(round(cost))
            if cost > best_cost.get(current, math.inf):
                continue

            for neighbour, edge_distance in self.adjacency[current]:
                new_cost = cost + edge_distance
                if new_cost < best_cost.get(neighbour, math.inf):
                    best_cost[neighbour] = new_cost
                    priority = new_cost + self._heuristic(neighbour, destination)
                    heapq.heappush(frontier, (priority, new_cost, neighbour, path + [neighbour]))
        return None
