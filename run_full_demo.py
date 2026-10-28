"""Run the complete intelligent classroom system with one click in VS Code."""

from __future__ import annotations

import json

from monitoring_system import ClassroomMonitoringSystem


def main() -> None:
    # No database is used in this demo so every run starts from a clean set of
    # five observations and produces predictable presentation results.
    system = ClassroomMonitoringSystem(database_path=None)
    result = system.process_scenario("overcrowded")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
