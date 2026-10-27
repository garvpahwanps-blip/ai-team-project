# Intelligent Classroom Occupancy and Utilization Agent

This repository currently contains the **intelligent-agent module** (Person 2).
It stores classroom and timetable data, remembers recent occupancy readings,
compares them with the current timetable, and produces a classroom decision.

## Run the sample flow

```bash
python -m agent.run_demo
```

The first normal run creates `data/classroom.db`, which stores occupancy and
status history using SQLite.

## Run tests

```bash
python -m unittest agent.test_agent -v
```

## Integration

The exact inputs and outputs shared with the detection, recommendation, and
dashboard modules are documented in [CONTRACT.md](CONTRACT.md).
