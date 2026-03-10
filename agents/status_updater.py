"""
Status Update Agent
===================
Final agent in the workflow. Writes completion status to:
  • Google Sheet (onboarding status column + processed flag)
  • PostgreSQL (employee status)
  • Console (summary log)
"""

from __future__ import annotations

import logging

from state import OnboardingState
from db.database import update_employee_status, update_task_status
from tools.google_sheets import update_sheet_status

logger = logging.getLogger(__name__)


# ── Agent Node ────────────────────────────────────────────────────────────────


def update_status(state: OnboardingState) -> dict:
    """LangGraph node — finalises the onboarding workflow."""
    logger.info(
        "▶ Status Update Agent — finalising onboarding for %s",
        state["employee_name"],
    )

    errors: list[str] = list(state.get("errors", []))
    has_critical_errors = any("ALERT" in e or "failed" in e.lower() for e in errors)
    final_status = "Completed" if not has_critical_errors else "Completed with Issues"

    # ── 1. Update PostgreSQL ──────────────────────────────────────────────
    employee_id = state.get("employee_id", "")
    if employee_id:
        try:
            update_employee_status(employee_id, final_status)
            logger.info("✔ Database status → %s", final_status)

            # Mark completed tasks
            for task_name in state.get("tasks_completed", []):
                try:
                    update_task_status(employee_id, task_name, "Completed")
                except Exception:
                    pass  # task might not exist in DB

        except Exception as exc:
            logger.error("✖ DB status update failed: %s", exc)
            errors.append(f"DB status update failed: {exc}")

    # ── 2. Update Google Sheet ────────────────────────────────────────────
    sheet_row = state.get("_sheet_row")
    if sheet_row:
        try:
            update_sheet_status(
                row_number=int(sheet_row),
                status=final_status,
                mark_processed=True,
            )
            logger.info("✔ Google Sheet row %s → %s", sheet_row, final_status)
        except Exception as exc:
            logger.error("✖ Sheet update failed: %s", exc)
            errors.append(f"Sheet status update failed: {exc}")

    # ── 3. Print Summary ─────────────────────────────────────────────────
    logger.info("=" * 60)
    logger.info("  ONBOARDING SUMMARY — %s", state["employee_name"])
    logger.info("=" * 60)
    logger.info("  Employee ID   : %s", state.get("employee_id", "N/A"))
    logger.info("  Role          : %s → %s", state.get("role", "N/A"), state.get("role_type", "N/A"))
    logger.info("  Department    : %s", state.get("department", "N/A"))
    logger.info("  Laptop        : %s", state.get("assigned_laptop", "N/A"))
    logger.info("  Meeting Link  : %s", state.get("meeting_link", "N/A"))
    logger.info("  Email Sent    : %s", "Yes" if state.get("email_sent") else "No")
    logger.info("  Tasks Done    : %s", ", ".join(state.get("tasks_completed", [])))
    logger.info("  Final Status  : %s", final_status)
    if errors:
        logger.info("  Errors        :")
        for err in errors:
            logger.info("    ⚠ %s", err)
    logger.info("=" * 60)

    return {
        "status": final_status,
        "errors": errors,
        "tasks_completed": state.get("tasks_completed", []) + ["Status Update"],
    }
