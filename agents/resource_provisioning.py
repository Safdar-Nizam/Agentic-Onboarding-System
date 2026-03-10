"""
Resource Provisioning Agent (Mock IT Agent)
===========================================
Simulates IT resource assignment:
  • Generate and persist an employee ID in PostgreSQL.
  • Assign the first available laptop from ``laptop_inventory``.
  • Simulate granting access to internal tools (GitHub, Jira, etc.).

If no laptops are available, a procurement alert is logged.
"""

from __future__ import annotations

import logging

from state import OnboardingState
from db.database import (
    insert_employee,
    assign_laptop,
    insert_onboarding_task,
    get_available_laptops,
)

logger = logging.getLogger(__name__)


# ── Agent Node ────────────────────────────────────────────────────────────────


def provision_resources(state: OnboardingState) -> dict:
    """LangGraph node — creates DB records and assigns hardware."""
    logger.info(
        "▶ Resource Provisioning Agent — provisioning for %s",
        state["employee_name"],
    )

    errors: list[str] = list(state.get("errors", []))
    employee_id = ""
    assigned_laptop = ""

    # ── 1. Create employee record ─────────────────────────────────────────
    try:
        employee_id = insert_employee(
            name=state["employee_name"],
            email=state["employee_email"],
            role=state["role"],
            department=state["department"],
            start_date=state.get("start_date", "2026-01-01"),
            manager=state.get("manager", "TBD"),
            location=state.get("location", "Remote"),
            employment_type=state.get("employment_type", "Full-time"),
        )
        logger.info("✔ Employee record created — %s", employee_id)
    except Exception as exc:
        logger.error("✖ Failed to create employee record: %s", exc)
        errors.append(f"Employee record creation failed: {exc}")

    # ── 2. Assign laptop ──────────────────────────────────────────────────
    if employee_id:
        try:
            available = get_available_laptops()
            logger.info("   Available laptops: %d", len(available))

            laptop_id = assign_laptop(employee_id)
            if laptop_id:
                assigned_laptop = laptop_id
                logger.info("✔ Laptop assigned — %s", laptop_id)
            else:
                msg = (
                    f"PROCUREMENT ALERT: No laptops available for "
                    f"{state['employee_name']} ({employee_id}). "
                    "Please order additional hardware."
                )
                logger.warning("⚠ %s", msg)
                errors.append(msg)

        except Exception as exc:
            logger.error("✖ Laptop assignment failed: %s", exc)
            errors.append(f"Laptop assignment failed: {exc}")

    # ── 3. Create onboarding task records ─────────────────────────────────
    if employee_id:
        plan = state.get("onboarding_plan", [])
        try:
            for task_name in plan:
                insert_onboarding_task(employee_id, task_name)
            logger.info("✔ %d onboarding tasks inserted into DB", len(plan))
        except Exception as exc:
            logger.error("✖ Task insertion failed: %s", exc)
            errors.append(f"Onboarding task insertion failed: {exc}")

    # ── 4. Simulate tool access ───────────────────────────────────────────
    provisioned_tools = state.get("required_resources", [])
    for tool_name in provisioned_tools:
        logger.info("   🔑 Simulated access granted → %s", tool_name)

    return {
        "employee_id": employee_id,
        "assigned_laptop": assigned_laptop,
        "errors": errors,
        "tasks_completed": state.get("tasks_completed", []) + ["Resource Provisioning"],
    }
