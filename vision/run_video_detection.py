"""Count students in the saved classroom video and run the full agent workflow.

Open this file in VS Code and press ▶ Run Python File after installing the
optional computer-vision requirements.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from monitoring_system import ClassroomMonitoringSystem
from vision.occupancy_detector import YOLOPersonCounter


def main() -> None:
    video = PROJECT_ROOT / "data" / "videos" / "classroomdemo.mp4"
    detector = YOLOPersonCounter()
    observations = detector.count_people_in_video(
        video_path=video,
        room_id="CSE-201",
        # Change this to match your actual lecture timetable when you use it live.
        timestamp="2026-10-27T10:30:00",
        samples=5,
    )
    system = ClassroomMonitoringSystem(PROJECT_ROOT / "data", database_path=None)
    result = system.process_observations(observations)
    result["video_file"] = str(video.relative_to(PROJECT_ROOT))
    result["video_observations"] = observations
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
