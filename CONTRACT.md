# Classroom Agent Integration Contract — Version 1

All modules use the exact room IDs in `data/classrooms.json` and ISO timestamps,
for example `2026-10-27T10:30:00`.

## Detection to intelligent agent

```json
{
  "room_id": "CSE-201",
  "detected_students": 55,
  "confidence": 0.91,
  "timestamp": "2026-10-27T10:30:00"
}
```

## Intelligent agent to dashboard

`ClassroomAgent.evaluate_room()` returns the result below. Its `stable_occupancy`
is the median of the most recent five readings for that room.

```json
{
  "room_id": "CSE-201",
  "detected_students": 55,
  "stable_occupancy": 54,
  "capacity": 40,
  "timetable_status": "SCHEDULED",
  "course_name": "Artificial Intelligence",
  "expected_students": 45,
  "classroom_state": "OVER_CROWDED",
  "alert": "Room capacity exceeded by 14 students.",
  "needs_alternative_room": true,
  "required_capacity": 54,
  "required_room_type": "CLASSROOM",
  "accessibility_required": false,
  "timestamp": "2026-10-27T10:30:00"
}
```

The approved states are `EMPTY`, `SCHEDULED_ACTIVE`, `UNSCHEDULED_USAGE`,
`UNDERUTILIZED`, `OVER_CROWDED`, and `UNAVAILABLE`.

## Intelligent agent to recommendation module

When `needs_alternative_room` is `true`, Person 3 needs the following fields
from the agent result: `room_id`, `classroom_state`, `required_capacity`,
`required_room_type`, `accessibility_required`, and `timestamp`.
