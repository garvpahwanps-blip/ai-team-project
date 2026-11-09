# Intelligent Classroom Occupancy and Utilization Agent

## What this project does
SmartClass AI helps a university understand how its classrooms are being used.
Give it a classroom video (or use a ready-made demonstration), and it will:
1. Count the students visible in the room.
2. Check whether a class is scheduled there and whether the room has enough seats.
3. Flag issues such as an overcrowded room or students using an unscheduled room.
4. Recommend the nearest suitable vacant classroom when a class needs to move.
The system remembers five camera readings before making a decision, so one unusual video frame does not control the result.
## Try the guided demo first — no video required
1. Start the dashboard with `streamlit run dashboard/app.py`.
2. Select **Simulated scenario** in the sidebar.
3. Keep **Overcrowded** selected and press **Run sample demo**.
4. The dashboard explains why CSE-201 is overcrowded and recommends a nearby vacant room.
## Project structure
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

## Live alternative-room status

The recommendation agent reads the live_room_status.json file every time it
searches for an alternative classroom. A room with current_occupancy above zero
is not recommended. In a real deployment, each classroom camera service would
update this shared status feed after processing a new observation.

## Integration

The exact inputs and outputs shared by each module are documented in [CONTRACT.md](CONTRACT.md).
