"""Connect the detection, intelligent-agent, and room-recommendation modules."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from agent.classroom_agent import ClassroomAgent
from recommendation.room_recommender import RoomRecommender
from vision.occupancy_detector import SimulatedOccupancyDetector


class ClassroomMonitoringSystem:
    """One orchestration point used by both the command-line demo and dashboard."""

    def __init__(
        self,
        data_directory: str | Path = "data",
        database_path: str | Path | None = None,
    ) -> None:
        directory = Path(data_directory)
        self.agent = ClassroomAgent(directory, database_path=database_path)
        self.detector = SimulatedOccupancyDetector(directory / "demo_observations.json")
        self.recommender = RoomRecommender(directory)

    def process_observations(self, observations: list[dict[str, Any]]) -> dict[str, Any]:
        """Run several camera readings through the agent, then obtain a route if needed."""
        if not observations:
            raise ValueError("At least one occupancy observation is required.")

        decision: dict[str, Any] | None = None
        for observation in observations:
            decision = self.agent.evaluate_room(**observation)
        assert decision is not None

        recommendation = None
        if decision["needs_alternative_room"]:
            request = {
                "source_room_id": decision["room_id"],
                "reason": decision["classroom_state"],
                "required_capacity": decision["required_capacity"],
                "required_room_type": decision["required_room_type"],
                "accessibility_required": decision["accessibility_required"],
                "timestamp": decision["timestamp"],
            }
            recommendation = self.recommender.recommend(
                request, {decision["room_id"]: decision["stable_occupancy"]}
            )

        return {
            "observations_processed": len(observations),
            "decision": decision,
            "recommendation": recommendation,
        }

    def process_scenario(self, scenario_name: str) -> dict[str, Any]:
        """Replay one prepared camera feed for the presentation/demo."""
        return self.process_observations(self.detector.get_observations(scenario_name))
