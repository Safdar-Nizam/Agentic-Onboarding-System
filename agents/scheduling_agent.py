"""
Scheduling Agent
================
Creates an orientation Zoom meeting for the new hire.
Includes retry logic (up to 3 attempts) and HR notification on failure.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from config import settings
from state import OnboardingState
from tools.zoom import create_meeting

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds


# ── Agent Node ────────────────────────────────────────────────────────────────


def schedule_orientation(state: OnboardingState) -> dict:
    """LangGraph node — creates a Zoom orientation meeting."""
    logger.info(
        "▶ Scheduling Agent — creating orientation for %s",
        state["employee_name"],
    )

    topic = (
        f"🎓 New Hire Orientation — {state['employee_name']} "
        f"({state['department']})"
    )
    agenda = (
        f"Welcome orientation for {state['employee_name']}\n"
        f"Role: {state['role']}\n"
        f"Department: {state['department']}\n"
        f"Manager: {state.get('manager', 'TBD')}\n\n"
        "Agenda:\n"
        "1. Welcome & introductions\n"
        "2. Company overview & culture\n"
        "3. Department walkthrough\n"
        "4. Tools & systems setup\n"
        "5. Q&A\n"
    )

    errors: list[str] = list(state.get("errors", []))
    meeting_link = ""
    meeting_details: dict[str, Any] = {}

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            meeting = create_meeting(
                topic=topic,
                duration_minutes=60,
                agenda=agenda,
            )
            meeting_link = meeting.get("join_url", "")
            meeting_details = {
                "meeting_id": meeting.get("id"),
                "join_url": meeting_link,
                "start_time": meeting.get("start_time"),
                "duration": meeting.get("duration"),
                "topic": topic,
                "password": meeting.get("password", ""),
            }
            logger.info("✔ Zoom meeting created — %s", meeting_link)
            break

        except Exception as exc:
            logger.warning(
                "✖ Zoom attempt %d/%d failed: %s",
                attempt, MAX_RETRIES, exc,
            )
            errors.append(f"Zoom attempt {attempt} failed: {exc}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)

    if not meeting_link:
        logger.error(
            "✖ All Zoom attempts failed for %s — HR should be notified.",
            state["employee_name"],
        )
        errors.append(
            f"ALERT: Zoom meeting creation failed for {state['employee_name']}. "
            "HR must schedule manually."
        )

    return {
        "meeting_link": meeting_link,
        "meeting_details": meeting_details,
        "errors": errors,
        "tasks_completed": state.get("tasks_completed", []) + ["Orientation Scheduling"],
    }
