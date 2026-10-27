"""Small SQLite store for observations and final agent decisions.

The project can run without a database during unit tests.  In normal use this
module makes the agent's occupancy history survive an application restart.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


class ObservationStore:
    """Persist occupancy readings and agent outcomes using Python's built-in SQLite."""

    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._create_tables()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _create_tables(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS occupancy_logs (
                    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    room_id TEXT NOT NULL,
                    detected_students INTEGER NOT NULL,
                    confidence REAL NOT NULL,
                    observed_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS room_status_logs (
                    status_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    room_id TEXT NOT NULL,
                    classroom_state TEXT NOT NULL,
                    stable_occupancy INTEGER NOT NULL,
                    alert TEXT NOT NULL,
                    evaluated_at TEXT NOT NULL
                );
                """
            )

    def record_observation(
        self, room_id: str, detected_students: int, confidence: float, timestamp: str
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO occupancy_logs (room_id, detected_students, confidence, observed_at)
                VALUES (?, ?, ?, ?)
                """,
                (room_id, detected_students, confidence, timestamp),
            )

    def recent_counts(self, room_id: str, limit: int) -> list[int]:
        """Return the most recent counts in oldest-to-newest order."""
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT detected_students
                FROM occupancy_logs
                WHERE room_id = ?
                ORDER BY log_id DESC
                LIMIT ?
                """,
                (room_id, limit),
            ).fetchall()
        return [int(row["detected_students"]) for row in reversed(rows)]

    def record_status(self, decision: dict[str, Any]) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO room_status_logs
                    (room_id, classroom_state, stable_occupancy, alert, evaluated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    decision["room_id"],
                    decision["classroom_state"],
                    decision["stable_occupancy"],
                    decision["alert"],
                    decision["timestamp"],
                ),
            )
