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


def fresh_system() -> ClassroomMonitoringSystem:
    """Create a clean agent so a selected scenario has exactly five readings."""
    return ClassroomMonitoringSystem(PROJECT_ROOT / "data", database_path=None)


@st.cache_data
def classroom_reference() -> list[dict[str, str | int]]:
    """Return friendly classroom details for faculty when selecting a room ID."""
    source = PROJECT_ROOT / "data" / "classrooms.json"
    rooms = json.loads(source.read_text(encoding="utf-8"))
    return [
        {
            "Room ID": room["room_id"],
            "Classroom name": room["room_name"],
            "Capacity": room["capacity"],
            "Type": room["room_type"].title(),
            "Location": f"{room['building']}, floor {room['floor']}",
            "Accessible": "Yes" if room["accessibility"] else "No",
            "Configured availability": "Available" if room["available"] else "Unavailable",
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
    st.session_state.result = fresh_system().process_scenario("normal")
    st.session_state.result_source = "Initial demonstration scenario"

with st.container(border=True):
    st.badge(
        "Five-frame intelligent monitoring",
        icon=":material/auto_awesome:",
        color="primary",
    )
    st.title("Classroom command center", icon=":material/sensors:")
    st.caption(
        "Turn a classroom video into an occupancy decision, timetable check, and room recommendation."
    )

run_upload = False
run_scenario = False
uploaded_video = None

with st.sidebar:
    st.header("Run an analysis", icon=":material/tune:")
    st.caption("Choose an input, then let the agent evaluate the classroom.")
    feed_type = st.segmented_control(
        "Feed source",
        ["Upload a video", "Simulated scenario"],
        default="Upload a video",
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
                "Camera-feed scenario",
                ["normal", "overcrowded", "unscheduled_usage", "empty", "unavailable_lab"],
                format_func=lambda item: item.replace("_", " ").title(),
            )
            run_scenario = st.form_submit_button(
                "Run simulated scenario",
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

with st.container(horizontal=True, vertical_alignment="center"):
    st.badge(state_label, icon=state_icon, color=state_colour)
    st.caption(st.session_state.result_source)

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
    st.subheader("Agent decision", icon=":material/psychology:")
    st.badge(state_label, icon=state_icon, color=state_colour)
    if state in {"OVER_CROWDED", "UNAVAILABLE"}:
        st.error(decision["alert"], title="Action required", icon=state_icon)
    elif state in {"UNSCHEDULED_USAGE", "UNDERUTILIZED"}:
        st.warning(decision["alert"], title="Review recommended", icon=state_icon)
    else:
        st.success(decision["alert"], title="Operating normally", icon=state_icon)

left, right = st.columns(2)
with left.container(border=True, height="stretch"):
    st.subheader("Room context", icon=":material/meeting_room:")
    st.write(f":material/door_front: **Room**  \\n+{decision['room_id']}")
    st.write(f":material/menu_book: **Scheduled course**  \\n+{decision['course_name'] or 'No class scheduled'}")
    st.write(f":material/groups: **Expected students**  \\n+{decision['expected_students'] or '—'}")
    st.write(f":material/visibility: **Latest camera count**  \\n+{decision['detected_students']}")
    st.write(f":material/verified: **Detection confidence**  \\n+{decision['confidence']:.0%}")

with right.container(border=True, height="stretch"):
    st.subheader("Alternative room", icon=":material/near_me:")
    recommendation = result["recommendation"]
    if recommendation and recommendation["alternative_found"]:
        st.success(
            recommendation["message"],
            title="Best available match",
            icon=":material/check_circle:",
        )
        st.metric(
            "Recommended room",
            recommendation["recommended_room_id"],
            border=True,
            icon=":material/meeting_room:",
        )
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

with st.expander("Technical integration data", icon=":material/data_object:"):
    st.json(result)

with st.container(border=True):
    st.subheader("Classroom directory", icon=":material/apartment:")
    st.caption("Use one of these room IDs when analysing an uploaded video.")
    st.dataframe(
        classroom_reference(),
        hide_index=True,
        width="stretch",
        alt="Reference table of all configured classrooms, capacities, types, locations, and accessibility.",
    )
