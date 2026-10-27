import json
from pathlib import Path
from typing import Any

import streamlit as st


ALLOWED_CLASSROOM_STATES = {
    "EMPTY",
    "SCHEDULED_ACTIVE",
    "UNSCHEDULED_USAGE",
    "UNDERUTILIZED",
    "OVER_CROWDED",
    "UNAVAILABLE",
}

STATUS_FILE = Path("outputs/status.json")
RECOMMENDATION_FILE = Path("outputs/recommendation.json")

DEMO_STATUS = {
    "room_id": "CSE-201",
    "stable_occupancy": 54,
    "capacity": 40,
    "timetable_status": "SCHEDULED",
    "course_name": "Artificial Intelligence",
    "classroom_state": "OVER_CROWDED",
    "alert": "Room capacity exceeded.",
    "needs_alternative_room": True,
}

DEMO_RECOMMENDATION = {
    "source_room_id": "CSE-201",
    "recommended_room_id": "CSE-305",
    "recommended_room_capacity": 60,
    "distance_meters": 120,
    "route": ["CSE-201", "Corridor-2", "Stairs-A", "CSE-305"],
    "message": "CSE-305 is the nearest suitable available classroom.",
}


def read_json_file(file_path: Path, default: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    if not file_path.exists():
        return default, False

    try:
        with file_path.open("r", encoding="utf-8") as file:
            value = json.load(file)
    except json.JSONDecodeError as error:
        raise ValueError(f"{file_path} contains invalid JSON: {error}") from error

    if not isinstance(value, dict):
        raise ValueError(f"{file_path} must contain one JSON object/dictionary.")
    return value, True


def validate_status(status: dict[str, Any]) -> list[str]:
    required_fields = {
        "room_id",
        "stable_occupancy",
        "capacity",
        "timetable_status",
        "course_name",
        "classroom_state",
        "alert",
        "needs_alternative_room",
    }
    errors = []
    missing_fields = required_fields - status.keys()
    if missing_fields:
        errors.append("Person 2 status is missing: " + ", ".join(sorted(missing_fields)))

    state = status.get("classroom_state")
    if state is not None and state not in ALLOWED_CLASSROOM_STATES:
        errors.append(
            "classroom_state must be one of: "
            + ", ".join(sorted(ALLOWED_CLASSROOM_STATES))
        )

    for field in ("stable_occupancy", "capacity"):
        if field in status and not isinstance(status[field], (int, float)):
            errors.append(f"{field} must be a number.")

    if "needs_alternative_room" in status and not isinstance(
            status["needs_alternative_room"], bool
    ):
        errors.append("needs_alternative_room must be true or false.")
    return errors


def validate_recommendation(recommendation: dict[str, Any]) -> list[str]:
    required_fields = {
        "source_room_id",
        "recommended_room_id",
        "recommended_room_capacity",
        "distance_meters",
        "route",
        "message",
    }
    errors = []
    missing_fields = required_fields - recommendation.keys()
    if missing_fields:
        errors.append(
            "Person 3 recommendation is missing: "
            + ", ".join(sorted(missing_fields))
        )
    if "route" in recommendation and not isinstance(recommendation["route"], list):
        errors.append("route must be a list of room/corridor names.")
    return errors


def state_color(state: str) -> str:
    return {
        "EMPTY": "#64748b",
        "SCHEDULED_ACTIVE": "#16a34a",
        "UNSCHEDULED_USAGE": "#f59e0b",
        "UNDERUTILIZED": "#0284c7",
        "OVER_CROWDED": "#dc2626",
        "UNAVAILABLE": "#7c3aed",
    }.get(state, "#475569")


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        .block-container { padding-top: 2rem; padding-bottom: 3rem; }
        [data-testid="stMetric"] {
            background: linear-gradient(135deg, #172554 0%, #1e3a8a 100%);
            border: 1px solid #334155;
            padding: 1rem 1.1rem;
            border-radius: 16px;
            box-shadow: 0 8px 20px rgba(15, 23, 42, .22);
        }
        [data-testid="stMetricLabel"] { color: #bfdbfe !important; }
        [data-testid="stMetricValue"] { color: #f8fafc !important; }
        .hero {
            padding: 1.5rem 1.7rem;
            border-radius: 22px;
            background: linear-gradient(110deg, #0f172a, #1d4ed8 55%, #0ea5e9);
            color: white;
            margin-bottom: 1rem;
            box-shadow: 0 12px 28px rgba(30, 64, 175, .28);
        }
        .hero h1 { margin: 0; font-size: 2.15rem; }
        .hero p { margin: .45rem 0 0; color: #dbeafe; }
        .state-pill {
            display: inline-block;
            padding: .42rem .85rem;
            border-radius: 999px;
            color: white;
            font-weight: 800;
            letter-spacing: .04em;
            font-size: .86rem;
        }
        .info-card {
            background: rgba(30, 41, 59, .72);
            border: 1px solid #334155;
            border-radius: 16px;
            padding: 1rem 1.1rem;
            min-height: 120px;
        }
        .info-card h4 { margin: 0 0 .55rem; color: #93c5fd; }
        .info-card p { margin: .3rem 0; }
        .route-step {
            border: 1px solid #2563eb;
            background: #172554;
            border-radius: 14px;
            padding: .75rem .5rem;
            text-align: center;
            font-weight: 700;
            min-height: 56px;
        }
        .route-arrow { text-align: center; font-size: 1.4rem; padding-top: .55rem; color: #60a5fa; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def show_state_pill(state: str) -> None:
    st.markdown(
        f'<span class="state-pill" style="background:{state_color(state)}">{state}</span>',
        unsafe_allow_html=True,
    )


def show_route(route: list[Any]) -> None:
    if not route:
        st.info("No route was provided.")
        return

    route_columns = st.columns(len(route) * 2 - 1)
    for index, item in enumerate(route):
        route_columns[index * 2].markdown(
            f'<div class="route-step">{item}</div>', unsafe_allow_html=True
        )
        if index < len(route) - 1:
            route_columns[index * 2 + 1].markdown(
                '<div class="route-arrow">→</div>', unsafe_allow_html=True
            )


def main() -> None:
    st.set_page_config(
        page_title="Smart Classroom Dashboard",
        page_icon="🏫",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inject_styles()

    with st.sidebar:
        st.markdown("## 🎛️ Dashboard controls")
        use_demo_data = st.toggle(
            "Use demo data",
            value=False,
            help="Turn this on only when the team JSON files are not available.",
        )
        if st.button("🔄 Refresh data", use_container_width=True, type="primary"):
            st.rerun()
        st.divider()
        st.markdown("### Data connection")
        st.success("Live JSON files" if not use_demo_data else "Demo mode")
        st.code("outputs/status.json\noutputs/recommendation.json")
        st.caption("Person 2 owns status.json. Person 3 owns recommendation.json.")

    try:
        if use_demo_data:
            status = DEMO_STATUS
            recommendation = DEMO_RECOMMENDATION
            status_from_file = recommendation_from_file = False
        else:
            status, status_from_file = read_json_file(STATUS_FILE, DEMO_STATUS)
            recommendation, recommendation_from_file = read_json_file(
                RECOMMENDATION_FILE, DEMO_RECOMMENDATION
            )
        validation_errors = validate_status(status) + validate_recommendation(recommendation)
    except ValueError as error:
        st.error(str(error))
        st.stop()

    if validation_errors:
        for error in validation_errors:
            st.error("Contract error: " + error)
        st.stop()

    if not status_from_file or not recommendation_from_file:
        st.warning("One or more live JSON files were not found. Demo values are being shown.")

    room_id = status["room_id"]
    occupancy = status["stable_occupancy"]
    capacity = status["capacity"]
    state = status["classroom_state"]
    utilization = (occupancy / capacity * 100) if capacity else 0
    needs_alternative_room = status["needs_alternative_room"]

    st.markdown(
        f"""
        <div class="hero">
            <h1>🏫 Smart Classroom Monitoring</h1>
            <p>Person 4 — Dashboard and Integration Module &nbsp;•&nbsp; Live room overview for <b>{room_id}</b></p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    title_col, state_col = st.columns([4, 1])
    with title_col:
        st.subheader(f"Room {room_id}")
        st.caption(f"Course: {status['course_name']}  •  Timetable: {status['timetable_status']}")
    with state_col:
        st.markdown("**Current state**")
        show_state_pill(state)

    metric_1, metric_2, metric_3, metric_4 = st.columns(4)
    metric_1.metric("👥 Student count", occupancy)
    metric_2.metric("🪑 Room capacity", capacity)
    metric_3.metric("📊 Utilization", f"{utilization:.1f}%")
    metric_4.metric("🗓️ Timetable", status["timetable_status"])

    progress_value = min(max(utilization / 100, 0.0), 1.0)
    st.progress(progress_value, text=f"Occupancy level: {utilization:.1f}%")

    overview_tab, route_tab, data_tab = st.tabs(
        ["📌 Overview", "🧭 Alternative room & route", "🔗 Integration data"]
    )

    with overview_tab:
        detail_col, alert_col = st.columns([1, 1])
        with detail_col:
            st.markdown(
                f"""
                <div class="info-card">
                    <h4>📚 Class details</h4>
                    <p><b>Course:</b> {status['course_name']}</p>
                    <p><b>Timetable:</b> {status['timetable_status']}</p>
                    <p><b>Classroom state:</b> {state}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with alert_col:
            st.markdown("#### 🚨 Alert centre")
            if status["alert"]:
                if state in {"OVER_CROWDED", "UNAVAILABLE"}:
                    st.error(status["alert"])
                else:
                    st.warning(status["alert"])
            else:
                st.success("No active alert for this room.")

        st.markdown("#### 📈 Capacity interpretation")
        if utilization > 100:
            st.error(f"This room is over capacity by {occupancy - capacity} students.")
        elif utilization < 50:
            st.info("This room is currently underutilized.")
        else:
            st.success("The room is being used within a normal range.")

    with route_tab:
        if needs_alternative_room:
            source_room = recommendation.get("source_room_id", room_id)
            recommended_room = recommendation.get("recommended_room_id", "Not available")
            route = recommendation.get("route", [])

            room_col, capacity_col, distance_col = st.columns(3)
            room_col.metric("✅ Recommended room", recommended_room)
            capacity_col.metric(
                "🪑 Recommended capacity",
                recommendation.get("recommended_room_capacity", "-"),
            )
            distance_col.metric(
                "📍 Walking distance",
                f"{recommendation.get('distance_meters', '-')} m",
            )

            if source_room != room_id:
                st.warning(
                    f"The recommendation source is {source_room}, but the current room is {room_id}."
                )
            st.info("💡 " + recommendation.get("message", "No recommendation message provided."))
            st.markdown("#### Route steps")
            show_route(route)
        else:
            st.success("✅ No alternative room is required for this observation.")

    with data_tab:
        st.caption("The dashboard displays the exact data received from Persons 2 and 3.")
        json_col_1, json_col_2 = st.columns(2)
        with json_col_1:
            st.markdown("#### Person 2 — status")
            st.json(status)
            st.download_button(
                "⬇️ Download status JSON",
                data=json.dumps(status, indent=2),
                file_name="status.json",
                mime="application/json",
                use_container_width=True,
            )
        with json_col_2:
            st.markdown("#### Person 3 — recommendation")
            st.json(recommendation)
            st.download_button(
                "⬇️ Download recommendation JSON",
                data=json.dumps(recommendation, indent=2),
                file_name="recommendation.json",
                mime="application/json",
                use_container_width=True,
            )

    st.divider()
    st.caption("Smart Classroom Monitoring System • Part 4 Dashboard and Integration")


if __name__ == "__main__":
    main()
