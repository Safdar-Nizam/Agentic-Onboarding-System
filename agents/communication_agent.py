"""
Communication Agent
===================
Generates a personalised welcome email using an LLM and sends it via the
Gmail API.  Includes retry logic (up to 3 attempts).
"""

from __future__ import annotations

import logging
import time

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from config import settings
from state import OnboardingState
from tools.gmail import send_welcome_email

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

# ── Prompt ────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a friendly HR communications specialist. Write a 
professional yet warm HTML welcome email for a new employee.

The email MUST include:
1. A personalized greeting using their name
2. A warm welcome message mentioning their role and department
3. Their start date and first-day instructions
4. The Zoom orientation meeting link (if provided)
5. A list of tools/resources they will receive access to
6. HR contact information for questions
7. An encouraging closing paragraph

Use clean, professional HTML with inline CSS styling. Use a modern, 
welcoming design. Output ONLY the HTML body — no <html> or <head> tags needed.
"""


# ── Agent Node ────────────────────────────────────────────────────────────────


def send_communication(state: OnboardingState) -> dict:
    """LangGraph node — generates and sends the welcome email."""
    logger.info(
        "▶ Communication Agent — composing welcome email for %s",
        state["employee_name"],
    )

    llm = ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        temperature=0.7,
    )

    meeting_link = state.get("meeting_link", "Will be shared separately")
    resources = state.get("required_resources", [])

    human_msg = (
        f"Write a welcome email for this new hire:\n"
        f"  Name: {state['employee_name']}\n"
        f"  Email: {state['employee_email']}\n"
        f"  Role: {state['role']}\n"
        f"  Department: {state['department']}\n"
        f"  Start Date: {state.get('start_date', 'TBD')}\n"
        f"  Manager: {state.get('manager', 'TBD')}\n"
        f"  Orientation Meeting Link: {meeting_link}\n"
        f"  Tools/Resources: {', '.join(resources)}\n"
        f"  HR Contact: {settings.gmail_sender_email}\n"
    )

    response = llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=human_msg),
    ])

    email_body = response.content
    subject = f"🎉 Welcome to the Team, {state['employee_name']}!"

    # ── Send with retries ─────────────────────────────────────────────────
    errors: list[str] = list(state.get("errors", []))
    email_sent = False

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            send_welcome_email(
                to=state["employee_email"],
                subject=subject,
                body_html=email_body,
            )
            email_sent = True
            logger.info("✔ Welcome email sent to %s (attempt %d)", state["employee_email"], attempt)
            break

        except Exception as exc:
            logger.warning(
                "✖ Email attempt %d/%d failed: %s",
                attempt, MAX_RETRIES, exc,
            )
            errors.append(f"Email attempt {attempt} failed: {exc}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)

    if not email_sent:
        logger.error("✖ All email attempts failed for %s", state["employee_email"])

    return {
        "email_sent": email_sent,
        "welcome_email_body": email_body,
        "errors": errors,
        "tasks_completed": state.get("tasks_completed", []) + ["Welcome Email"],
    }
