"""
Shared Workflow State
=====================
TypedDict that flows through every node in the LangGraph onboarding workflow.
Each agent reads from and writes to this shared state object.
"""

from __future__ import annotations

from typing import Annotated, Any
from typing_extensions import TypedDict

from langgraph.graph.message import add_messages


class OnboardingState(TypedDict, total=False):
    """Central state object shared across all onboarding agents.

    Fields marked with Annotated[..., add_messages] support LangGraph's
    built-in message accumulation for chat-style agent interactions.
    """

    # ── Employee Info (set by trigger) ────────────────────────────────────
    employee_name: str
    employee_email: str
    role: str
    department: str
    start_date: str
    manager: str
    location: str
    employment_type: str

    # ── Role Classification (set by Role Classifier) ─────────────────────
    role_type: str                    # e.g. "Engineering", "Marketing"
    required_resources: list[str]     # e.g. ["GitHub", "Jira", "AWS"]

    # ── Onboarding Plan (set by Planner) ─────────────────────────────────
    onboarding_plan: list[str]        # ordered checklist items

    # ── Resource Provisioning (set by IT Agent) ──────────────────────────
    employee_id: str                  # generated EMP-XXXXXXXX
    assigned_laptop: str              # e.g. "LPT-003"

    # ── Scheduling (set by Scheduling Agent) ─────────────────────────────
    meeting_link: str                 # Zoom join URL
    meeting_details: dict[str, Any]   # full meeting payload

    # ── Communication (set by Communication Agent) ───────────────────────
    email_sent: bool
    welcome_email_body: str           # LLM-generated email content

    # ── Progress Tracking ─────────────────────────────────────────────────
    tasks_completed: list[str]
    status: str                       # Pending | In Progress | Completed

    # ── Error Tracking ────────────────────────────────────────────────────
    errors: list[str]

    # ── Chat Messages (for agent reasoning; auto-accumulated) ─────────────
    messages: Annotated[list, add_messages]
