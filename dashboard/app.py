"""Streamlit dashboard for the complete classroom monitoring system.

Start it with: streamlit run dashboard/app.py
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agent.live_status import load_live_room_status
from monitoring_system import ClassroomMonitoringSystem
from vision.occupancy_detector import YOLOPersonCounter


ALLOWED_VIDEO_SUFFIXES = frozenset({".mp4", ".mov", ".avi", ".mkv", ".webm"})
STATE_PRESENTATION = {
    "EMPTY": ("Room clear", "green", ":material/check_circle:"),
    "SCHEDULED_ACTIVE": ("Scheduled class active", "blue", ":material/play_circle:"),
    "UNSCHEDULED_USAGE": ("Unscheduled usage", "orange", ":material/warning:"),
    "UNDERUTILIZED": ("Low utilisation", "yellow", ":material/trending_down:"),
    "OVER_CROWDED": ("Over capacity", "red", ":material/groups:"),
    "UNAVAILABLE": ("Room unavailable", "violet", ":material/block:"),
}
PLAIN_LANGUAGE_SUMMARIES = {
    "EMPTY": "The room is currently empty, so there is no capacity problem to solve.",
    "SCHEDULED_ACTIVE": "The camera count matches a scheduled class and the room has enough seats.",
    "UNSCHEDULED_USAGE": "Students are in the room, but the timetable has no class scheduled there.",
    "UNDERUTILIZED": "A scheduled class is running, but far fewer students are present than expected.",
    "OVER_CROWDED": "Too many students are in the room, so the system looks for a nearby vacant alternative.",
    "UNAVAILABLE": "This room cannot be used for its scheduled class, so the system searches for a replacement.",
}


def fresh_system() -> ClassroomMonitoringSystem:
    """Create a clean agent so a selected scenario has exactly five readings."""
    return ClassroomMonitoringSystem(PROJECT_ROOT / "data", database_path=None)


@st.cache_data
def classroom_reference(
    source_modified_at: int, live_status_modified_at: int
) -> list[dict[str, str | int]]:
    """Return friendly classroom details for faculty when selecting a room ID."""
    del source_modified_at, live_status_modified_at
    source = PROJECT_ROOT / "data" / "classrooms.json"
    rooms = json.loads(source.read_text(encoding="utf-8"))
    live_statuses = load_live_room_status(PROJECT_ROOT / "data")
    return [
        {
            "Room ID": room["room_id"],
            "Classroom name": room["room_name"],
            "Capacity": room["capacity"],
            "Type": room["room_type"].title(),
            "Building": room["building"],
            "Floor": room["floor"],
            "Accessible": "Yes" if room["accessibility"] else "No",
            "Configured availability": "Available" if room["available"] else "Unavailable",
            "Live occupancy": live_statuses.get(room["room_id"], {}).get(
                "current_occupancy", 0
            ),
            "Live status": live_statuses.get(room["room_id"], {}).get("state", "UNKNOWN"),
            "Last status update": live_statuses.get(room["room_id"], {}).get(
                "last_updated", "Not reported"
            ),
        }
        for room in rooms
    ]


@st.cache_resource(show_spinner=False)
def get_detector() -> YOLOPersonCounter:
    """Load YOLO once and reuse it for video uploads in this dashboard session."""
    return YOLOPersonCounter()


def process_uploaded_video(uploaded_video: object, room_id: str, timestamp: str) -> dict:
    """Analyse an uploaded video without saving it permanently in the project."""
    filename = getattr(uploaded_video, "name", "")
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_VIDEO_SUFFIXES:
        allowed = ", ".join(sorted(ALLOWED_VIDEO_SUFFIXES))
        raise ValueError(f"Upload one of these video types: {allowed}.")

    with tempfile.TemporaryDirectory(prefix="classroom-video-") as temporary_directory:
        temporary_path = Path(temporary_directory) / f"classroom_upload{suffix}"
        temporary_path.write_bytes(uploaded_video.getvalue())
        observations = get_detector().count_people_in_video(
            video_path=temporary_path,
            room_id=room_id.strip().upper(),
            timestamp=timestamp.strip(),
            samples=5,
        )

    return fresh_system().process_observations(observations)


st.set_page_config(
    page_title="Classroom command center",
    page_icon=":material/sensors:",
    layout="wide",
)

if "result" not in st.session_state:
    st.session_state.result = fresh_system().process_scenario("overcrowded")
    st.session_state.result_source = "Guided demo: overcrowded classroom (sample data)"

with st.container(border=True):
    st.badge(
        "Built for faculty and campus teams",
        icon=":material/auto_awesome:",
        color="primary",
    )
    st.title("SmartClass AI", icon=":material/sensors:")
    st.subheader("Know which classrooms are free, crowded, or being used without a booking.")
    st.write("Upload a classroom video, and the system counts students, checks the timetable, and suggests a suitable room when action is needed.")
    st.info("Start with the guided demo in the sidebar. It shows the full journey without needing a video.", title="New to this project?", icon=":material/tips_and_updates:")
with st.container(border=True):
    st.subheader("How it works", icon=":material/account_tree:")
    step_columns = st.columns(3)
    with step_columns[0].container(border=True, height="stretch"):
        st.markdown(":material/videocam: **1. Count students**")
        st.caption("The camera feed or uploaded video is sampled at five points to estimate how many students are present.")
    with step_columns[1].container(border=True, height="stretch"):
        st.markdown(":material/psychology: **2. Check the situation**")
        st.caption("The agent compares the count with room capacity and the timetable. It remembers five readings instead of trusting one frame.")
    with step_columns[2].container(border=True, height="stretch"):
        st.markdown(":material/near_me: **3. Recommend a room**")
        st.caption("If the room is crowded or unavailable, the system finds the closest suitable room that is currently vacant.")
with st.expander("What does the system check before recommending another room?", icon=":material/help:"):
    st.write("It checks seating capacity, room type, accessibility, building/floor, timetable availability, live occupancy, and walking distance.")

run_upload = False
run_scenario = False
uploaded_video = None

with st.sidebar:
    st.header("Start an analysis", icon=":material/tune:")
    st.info("Select **Simulated scenario**, keep **Overcrowded**, then choose **Run sample demo**. You will see a complete recommendation without uploading a video.", title="Try this first", icon=":material/play_circle:")
    feed_type = st.segmented_control(
        "How would you like to test it?",
        ["Upload a video", "Simulated scenario"],
        default="Simulated scenario",
        required=True,
        width="stretch",
        key="feed_source",
    )

    if feed_type == "Upload a video":
        with st.form("uploaded_video_form"):
            uploaded_video = st.file_uploader(
                "Upload a classroom video",
                type=[suffix.removeprefix(".") for suffix in sorted(ALLOWED_VIDEO_SUFFIXES)],
                max_upload_size=100,
                help="Use a short classroom recording. The app samples five frames from it.",
                key="classroom_video_upload",
            )
            video_room = st.text_input("Room ID", "CSE-201")
            video_timestamp = st.text_input("Lecture timestamp", "2026-10-27T10:30:00")
            run_upload = st.form_submit_button(
                "Analyse uploaded video",
                type="primary",
                icon=":material/analytics:",
                width="stretch",
            )
        st.info(
            "Your video stays on this computer and is deleted after analysis.",
            title="Private processing",
            icon=":material/lock:",
        )
    else:
        with st.form("simulated_scenario_form"):
            scenario = st.selectbox(
                "Sample classroom situation",
                ["normal", "overcrowded", "unscheduled_usage", "empty", "unavailable_lab"],
                index=1,
                format_func=lambda item: item.replace("_", " ").title(),
            )
            run_scenario = st.form_submit_button(
                "Run sample demo",
                type="primary",
                icon=":material/play_arrow:",
                width="stretch",
            )
        st.info(
            "Each demo uses five readings, so the agent does not decide from one frame.",
            title="Model-based decision",
            icon=":material/psychology:",
        )

if feed_type == "Upload a video" and run_upload:
    if uploaded_video is None:
        st.error("Choose a classroom video before selecting Analyse uploaded video.")
    elif not video_room.strip() or not video_timestamp.strip():
        st.error("Enter both a room ID and a lecture timestamp.")
    else:
        try:
            with st.spinner("Analysing five video frames with YOLO..."):
                st.session_state.result = process_uploaded_video(
                    uploaded_video,
                    video_room,
                    video_timestamp,
                )
                st.session_state.result_source = f"Uploaded video: {uploaded_video.name}"
        except (FileNotFoundError, OSError, RuntimeError, ValueError) as error:
            st.error(str(error))
elif feed_type == "Simulated scenario" and run_scenario:
    st.session_state.result = fresh_system().process_scenario(scenario)
    st.session_state.result_source = f"Simulated scenario: {scenario.replace('_', ' ')}"

result = st.session_state.result
decision = result["decision"]
state = decision["classroom_state"]
state_label, state_colour, state_icon = STATE_PRESENTATION.get(
    state, (state.replace("_", " ").title(), "gray", ":material/info:")
)
plain_summary = PLAIN_LANGUAGE_SUMMARIES.get(
    state, "The system evaluated the camera reading, room details, and timetable information."
)

with st.container(horizontal=True, vertical_alignment="center"):
    st.badge(state_label, icon=state_icon, color=state_colour)
    st.caption(st.session_state.result_source)
st.caption("The result below answers two questions: Is this classroom okay to use right now? If not, where should the class go?")

metrics = st.columns(4)
metrics[0].metric(
    "Detected students",
    decision["stable_occupancy"],
    border=True,
    height="stretch",
    icon=":material/groups:",
)
metrics[1].metric(
    "Room capacity",
    decision["capacity"],
    border=True,
    height="stretch",
    icon=":material/event_seat:",
)
metrics[2].metric(
    "Timetable",
    decision["timetable_status"].replace("_", " ").title(),
    border=True,
    height="stretch",
    icon=":material/calendar_month:",
)
metrics[3].metric(
    "Frames analysed",
    result["observations_processed"],
    border=True,
    height="stretch",
    icon=":material/movie:",
)

with st.container(border=True):
    st.subheader("What the system found", icon=":material/psychology:")
    st.badge(state_label, icon=state_icon, color=state_colour)
    if state in {"OVER_CROWDED", "UNAVAILABLE"}:
        st.error(decision["alert"], title="Action required", icon=state_icon)
    elif state in {"UNSCHEDULED_USAGE", "UNDERUTILIZED"}:
        st.warning(decision["alert"], title="Review recommended", icon=state_icon)
    else:
        st.success(decision["alert"], title="Operating normally", icon=state_icon)
    st.caption(plain_summary)
    st.caption("The decision is based on the middle value from five camera readings, so one unusual frame does not control the result.")

left, right = st.columns(2)
with left.container(border=True, height="stretch"):
    st.subheader("What the camera and timetable say", icon=":material/meeting_room:")
    st.write(f":material/door_front: **Room:** {decision['room_id']}")
    st.write(f":material/menu_book: **Scheduled course:** {decision['course_name'] or 'No class scheduled'}")
    st.write(f":material/groups: **Expected students:** {decision['expected_students'] or '—'}")
    st.write(f":material/visibility: **Latest camera count:** {decision['detected_students']}")
    st.write(f":material/verified: **Detection confidence:** {decision['confidence']:.0%}")

with right.container(border=True, height="stretch"):
    st.subheader("Where the class should go", icon=":material/near_me:")
    recommendation = result["recommendation"]
    if recommendation and recommendation["alternative_found"]:
        st.success(
            recommendation["message"],
            title="Best available match",
            icon=":material/check_circle:",
        )
        st.caption("This room matches the required capacity and type, is currently vacant, and has the shortest suitable campus route.")
        st.metric(
            "Recommended room",
            recommendation["recommended_room_id"],
            border=True,
            icon=":material/meeting_room:",
        )
        live_occupancy = recommendation.get("recommended_room_current_occupancy")
        if live_occupancy is None:
            st.caption("Live occupancy has not been reported for this room yet.")
        else:
            st.write(f":material/sensors: **Live occupancy:** {live_occupancy} students")
        st.write(f":material/event_seat: **Capacity:** {recommendation['recommended_room_capacity']}")
        st.write(f":material/directions_walk: **Walking distance:** {recommendation['distance_meters']} m")
        st.code("  →  ".join(recommendation["route"]), language=None)
    elif recommendation:
        st.error(recommendation["message"], title="No suitable alternative", icon=":material/error:")
    else:
        st.info(
            "No alternative classroom is required for this condition.",
            title="No relocation needed",
            icon=":material/check_circle:",
        )

with st.expander("For developers: view raw system data", icon=":material/data_object:"):
    st.json(result)

with st.container(border=True):
    st.subheader("Explore classrooms on campus", icon=":material/apartment:")
    st.caption("Use this reference list to compare room capacities, locations, facilities, and current occupancy.")
    classrooms_source = PROJECT_ROOT / "data" / "classrooms.json"
    live_status_source = PROJECT_ROOT / "data" / "live_room_status.json"
    directory_rows = classroom_reference(
        classrooms_source.stat().st_mtime_ns, live_status_source.stat().st_mtime_ns
    )
    buildings = sorted({str(room["Building"]) for room in directory_rows})
    room_types = sorted({str(room["Type"]) for room in directory_rows})

    building_filter, type_filter = st.columns(2)
    selected_buildings = building_filter.multiselect(
        "Building",
        buildings,
        default=buildings,
        key="directory_building_filter",
    )
    selected_room_types = type_filter.multiselect(
        "Room type",
        room_types,
        default=room_types,
        key="directory_type_filter",
    )
    visible_rooms = [
        room
        for room in directory_rows
        if room["Building"] in selected_buildings and room["Type"] in selected_room_types
    ]

    directory_metrics = st.columns(4)
    directory_metrics[0].metric(
        "Rooms shown",
        len(visible_rooms),
        border=True,
        icon=":material/meeting_room:",
    )
    directory_metrics[1].metric(
        "Total seats",
        sum(int(room["Capacity"]) for room in visible_rooms),
        border=True,
        icon=":material/event_seat:",
    )
    directory_metrics[2].metric(
        "Accessible rooms",
        sum(room["Accessible"] == "Yes" for room in visible_rooms),
        border=True,
        icon=":material/accessibility_new:",
    )
    directory_metrics[3].metric(
        "Rooms in use",
        sum(int(room["Live occupancy"]) > 0 for room in visible_rooms),
        border=True,
        icon=":material/sensors:",
    )
    st.dataframe(
        visible_rooms,
        hide_index=True,
        width="stretch",
        alt="Classroom directory showing configured rooms, capacities, types, buildings, and accessibility.",
    )
