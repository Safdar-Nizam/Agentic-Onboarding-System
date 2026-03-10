"""
Onboarding Plan Agent
=====================
Generates a structured onboarding checklist tailored to the employee's
role type, department, and employment type.  The plan becomes the execution
blueprint for all downstream agents.
"""

from __future__ import annotations

import json
import logging

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from config import settings
from state import OnboardingState

logger = logging.getLogger(__name__)

# ── Prompt ────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are an onboarding planning specialist. Given information 
about a new employee, generate a comprehensive onboarding checklist.

The checklist must ALWAYS include these core items (adapt descriptions as needed):
1. Send personalized welcome email
2. Schedule orientation meeting via Zoom
3. Assign laptop and equipment from IT inventory
4. Provision required software and tool access
5. Create employee ID and database record
6. Notify hiring manager of onboarding progress
7. Provide department-specific documentation and training materials
8. Set up first-week check-in meetings
9. Complete compliance and policy acknowledgements
10. Final onboarding status review

You may add 2-5 additional role-specific items depending on the role type.

Respond ONLY with valid JSON — no markdown, no explanation:
{
  "onboarding_plan": [
    "Task description 1",
    "Task description 2",
    ...
  ]
}
"""


# ── Agent Node ────────────────────────────────────────────────────────────────


def generate_onboarding_plan(state: OnboardingState) -> dict:
    """LangGraph node — generates the onboarding task checklist."""
    logger.info(
        "▶ Onboarding Plan Agent — building plan for %s (role_type=%s)",
        state["employee_name"],
        state.get("role_type", "Unknown"),
    )

    llm = ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        temperature=0.3,
    )

    human_msg = (
        f"Employee: {state['employee_name']}\n"
        f"Role: {state['role']}\n"
        f"Role Type: {state.get('role_type', 'General')}\n"
        f"Department: {state['department']}\n"
        f"Employment Type: {state.get('employment_type', 'Full-time')}\n"
        f"Required Resources: {', '.join(state.get('required_resources', []))}\n"
        f"Start Date: {state.get('start_date', 'TBD')}\n"
    )

    response = llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=human_msg),
    ])

    try:
        result = json.loads(response.content)
        onboarding_plan = result["onboarding_plan"]
    except (json.JSONDecodeError, KeyError) as exc:
        logger.warning("LLM returned unparseable plan, using defaults: %s", exc)
        onboarding_plan = [
            "Send personalized welcome email",
            "Schedule orientation meeting via Zoom",
            "Assign laptop and equipment",
            "Provision software access",
            "Create employee ID",
            "Notify hiring manager",
            "Provide department documentation",
            "Set up first-week check-ins",
            "Complete compliance acknowledgements",
            "Final onboarding review",
        ]

    logger.info(
        "✔ Onboarding plan generated — %d tasks",
        len(onboarding_plan),
    )
    for i, task in enumerate(onboarding_plan, 1):
        logger.info("   %2d. %s", i, task)

    return {
        "onboarding_plan": onboarding_plan,
        "tasks_completed": state.get("tasks_completed", []) + ["Onboarding Plan Generation"],
    }
