"""Run a simulated student-detection feed directly from VS Code's Run button."""

from __future__ import annotations

import json
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from vision.occupancy_detector import SimulatedOccupancyDetector
else:
    from .occupancy_detector import SimulatedOccupancyDetector


def main() -> None:
    detector = SimulatedOccupancyDetector()
    print(json.dumps(detector.get_observations("overcrowded"), indent=2))


if __name__ == "__main__":
    main()
