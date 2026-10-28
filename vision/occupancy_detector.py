"""Turn a classroom feed into the observation shared with the intelligent agent."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class SimulatedOccupancyDetector:
    """Replay named classroom-feed scenarios so the whole project can be demoed offline."""

    def __init__(self, scenario_path: str | Path = "data/demo_observations.json") -> None:
        source = Path(scenario_path)
        self.scenarios: dict[str, dict[str, Any]] = json.loads(source.read_text(encoding="utf-8"))

    def available_scenarios(self) -> list[str]:
        return sorted(self.scenarios)

    def get_observations(self, scenario_name: str) -> list[dict[str, Any]]:
        """Return a sequence of detection messages in the agreed integration format."""
        if scenario_name not in self.scenarios:
            choices = ", ".join(self.available_scenarios())
            raise ValueError(f"Unknown scenario '{scenario_name}'. Choose one of: {choices}")

        scenario = self.scenarios[scenario_name]
        return [
            {
                "room_id": scenario["room_id"],
                "detected_students": int(count),
                "confidence": float(scenario["confidence"]),
                "timestamp": scenario["timestamp"],
            }
            for count in scenario["counts"]
        ]


class YOLOPersonCounter:
    """Optional real image/video person counter backed by Ultralytics YOLO.

    Install `ultralytics` and `opencv-python` before using this class.  It counts
    people in one frame; the classroom agent handles smoothing across frames.
    """

    def __init__(self, model_name: str = "yolo11n.pt", confidence_threshold: float = 0.35) -> None:
        try:
            import cv2
            from ultralytics import YOLO
        except ImportError as error:
            raise RuntimeError(
                "Real video detection needs `pip install ultralytics opencv-python`. "
                "Use the simulated detector until then."
            ) from error

        self.cv2 = cv2
        self.model = YOLO(model_name)
        self.confidence_threshold = confidence_threshold

    def _count_people(self, frame: Any) -> tuple[int, float]:
        """Return people count and mean detection confidence for a single frame."""
        result = self.model(
            frame, classes=[0], conf=self.confidence_threshold, verbose=False
        )[0]
        confidences = result.boxes.conf.tolist() if result.boxes and result.boxes.conf is not None else []
        average_confidence = round(sum(confidences) / len(confidences), 3) if confidences else 0.0
        return len(confidences), average_confidence

    def count_people_in_image(
        self,
        *,
        image_path: str | Path,
        room_id: str,
        timestamp: str,
    ) -> dict[str, Any]:
        """Count people in an image and return the standard observation dictionary."""
        image = self.cv2.imread(str(image_path))
        if image is None:
            raise FileNotFoundError(f"Could not read image: {image_path}")
        count, average_confidence = self._count_people(image)
        return {
            "room_id": room_id,
            "detected_students": count,
            "confidence": average_confidence,
            "timestamp": timestamp,
        }

    def count_people_in_video(
        self,
        *,
        video_path: str | Path,
        room_id: str,
        timestamp: str,
        samples: int = 5,
    ) -> list[dict[str, Any]]:
        """Sample frames across a video and return one shared-format observation per frame.

        The intelligent agent consumes the returned sequence and uses its median,
        which prevents one blurry frame from causing an incorrect room decision.
        """
        source = Path(video_path)
        if not source.is_file():
            raise FileNotFoundError(f"Could not find video: {source}")
        if samples < 1:
            raise ValueError("samples must be at least 1.")

        capture = self.cv2.VideoCapture(str(source))
        if not capture.isOpened():
            raise ValueError(f"Could not open video: {source}")
        try:
            frame_total = int(capture.get(self.cv2.CAP_PROP_FRAME_COUNT))
            if frame_total < 1:
                raise ValueError("The video contains no readable frames.")
            positions = sorted(
                {
                    round(index * (frame_total - 1) / max(samples - 1, 1))
                    for index in range(samples)
                }
            )
            observations: list[dict[str, Any]] = []
            for frame_number in positions:
                capture.set(self.cv2.CAP_PROP_POS_FRAMES, frame_number)
                ok, frame = capture.read()
                if not ok:
                    continue
                count, average_confidence = self._count_people(frame)
                observations.append(
                    {
                        "room_id": room_id,
                        "detected_students": count,
                        "confidence": average_confidence,
                        "timestamp": timestamp,
                    }
                )
            if not observations:
                raise ValueError("No usable frames were detected in the video.")
            return observations
        finally:
            capture.release()
