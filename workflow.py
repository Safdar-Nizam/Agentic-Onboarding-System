"""
LangGraph Onboarding Workflow
=============================
Constructs and compiles the multi-agent StateGraph that orchestrates the
entire employee onboarding process.

Graph Flow
----------
START → role_classifier → onboarding_planner → resource_provisioning
      → scheduling_agent → communication_agent → status_updater → END

Error-aware conditional edges route to the status updater early if a
critical failure is detected.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from langgraph.graph import StateGraph, START, END

from state import OnboardingState
from agents.role_classifier import classify_role
from agents.onboarding_planner import generate_onboarding_plan
from agents.communication_agent import send_communication
from agents.scheduling_agent import schedule_orientation
from agents.resource_provisioning import provision_resources
from agents.status_updater import update_status

logger = logging.getLogger(__name__)


# ── Conditional Edge Helpers ──────────────────────────────────────────────────


def _should_continue_after_provisioning(state: OnboardingState) -> str:
    """Check for critical provisioning failures before continuing."""
    errors = state.get("errors", [])
    critical = any("ALERT" in e for e in errors)
    if critical and not state.get("employee_id"):
        logger.warning("⚠ Critical provisioning failure — skipping to status update.")
        return "status_updater"
    return "scheduling_agent"


def _should_continue_after_scheduling(state: OnboardingState) -> str:
    """Always continue to communication — meeting link is optional."""
    return "communication_agent"


# ── Graph Builder ─────────────────────────────────────────────────────────────


def build_graph() -> StateGraph:
    """Construct the LangGraph workflow and return the compiled graph.

    The graph connects six specialised agents in sequence with conditional
    routing after the resource provisioning step.
    """
    logger.info("Building LangGraph onboarding workflow …")

    graph = StateGraph(OnboardingState)

    # ── Add Nodes ─────────────────────────────────────────────────────────
    graph.add_node("role_classifier", classify_role)
    graph.add_node("onboarding_planner", generate_onboarding_plan)
    graph.add_node("resource_provisioning", provision_resources)
    graph.add_node("scheduling_agent", schedule_orientation)
    graph.add_node("communication_agent", send_communication)
    graph.add_node("status_updater", update_status)

    # ── Add Edges ─────────────────────────────────────────────────────────
    # Linear flow with conditional branching after provisioning
    graph.add_edge(START, "role_classifier")
    graph.add_edge("role_classifier", "onboarding_planner")
    graph.add_edge("onboarding_planner", "resource_provisioning")

    # Conditional: skip to status_updater if provisioning critically fails
    graph.add_conditional_edges(
        "resource_provisioning",
        _should_continue_after_provisioning,
        {
            "scheduling_agent": "scheduling_agent",
            "status_updater": "status_updater",
        },
    )

    graph.add_edge("scheduling_agent", "communication_agent")
    graph.add_edge("communication_agent", "status_updater")
    graph.add_edge("status_updater", END)

    logger.info("✔ Workflow graph compiled successfully.")
    return graph.compile()


# ── Runner ────────────────────────────────────────────────────────────────────


def run_onboarding(employee_data: dict[str, Any]) -> dict[str, Any]:
    """Execute the full onboarding workflow for a single new hire.

    Parameters
    ----------
    employee_data : dict
        Must contain at minimum: employee_name, employee_email, role,
        department, start_date, manager.

    Returns
    -------
    dict
        The final state after all agents have run.
    """
    start_time = time.time()

    initial_state: dict[str, Any] = {
        "employee_name": employee_data.get("employee_name", ""),
        "employee_email": employee_data.get("employee_email", ""),
        "role": employee_data.get("role", ""),
        "department": employee_data.get("department", ""),
        "start_date": employee_data.get("start_date", ""),
        "manager": employee_data.get("manager", ""),
        "location": employee_data.get("location", "Remote"),
        "employment_type": employee_data.get("employment_type", "Full-time"),
        "role_type": "",
        "required_resources": [],
        "onboarding_plan": [],
        "employee_id": "",
        "assigned_laptop": "",
        "meeting_link": "",
        "meeting_details": {},
        "email_sent": False,
        "welcome_email_body": "",
        "tasks_completed": [],
        "status": "In Progress",
        "errors": [],
        "messages": [],
        "_sheet_row": employee_data.get("_sheet_row", ""),
    }

    logger.info("=" * 60)
    logger.info("  STARTING ONBOARDING — %s", initial_state["employee_name"])
    logger.info("  Role: %s | Dept: %s", initial_state["role"], initial_state["department"])
    logger.info("=" * 60)

    compiled_graph = build_graph()
    final_state = compiled_graph.invoke(initial_state)

    elapsed = time.time() - start_time
    logger.info(
        "Onboarding workflow completed in %.2f seconds for %s",
        elapsed,
        initial_state["employee_name"],
    )

    return final_state
