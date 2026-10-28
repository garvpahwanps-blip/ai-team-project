# Intelligent Classroom Occupancy and Utilization Agent

A four-part university classroom monitoring project:

1. `vision/` detects or simulates the number of people in a classroom.
2. `agent/` remembers five readings, checks the timetable, and decides the room state.
3. `recommendation/` filters suitable rooms and uses A* to find the nearest route.
4. `dashboard/` displays the result for faculty and administrators.

## Fastest way to run the whole project

Open `run_full_demo.py` in VS Code and press the normal **▶ Run Python File** button.
It replays an overcrowded camera feed and recommends `CSE-305`.

Or use the terminal from the project folder:

```bash
python3 run_full_demo.py
```

## Run all tests

```bash
python3 -m unittest discover -v
```

## Run the dashboard

Install the dashboard package once:

```bash
python3 -m pip install streamlit
```

Then start the faculty dashboard:

```bash
streamlit run dashboard/app.py
```

In the dashboard, select **Upload a video**, choose a short classroom recording,
enter its room ID and lecture timestamp, then select **Analyse uploaded video**.
The app samples five frames, counts people with YOLO, checks the timetable and
capacity, and shows any alternative-room recommendation. Uploaded videos are
processed locally and deleted automatically; you do not need to copy them into
the project folder.

To connect a real classroom image/video feed later, also install:

```bash
python3 -m pip install ultralytics opencv-python
```

The `YOLOPersonCounter` in `vision/occupancy_detector.py` then produces the same
observation format used by the rest of the project.

## Run real video detection

Save a classroom video as `data/videos/classroomdemo.mp4`, then run:

```bash
.venv/bin/python vision/run_video_detection.py
```

The program samples five frames across the video, uses YOLO to count people in
each frame, and passes those readings to the intelligent agent. This is an
optional command-line alternative to using the dashboard upload feature.

Video files and downloaded YOLO model weights are intentionally ignored by Git.

## Integration

The exact inputs and outputs shared by each module are documented in [CONTRACT.md](CONTRACT.md).
