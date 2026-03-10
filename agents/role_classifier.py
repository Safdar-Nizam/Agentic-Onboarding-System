"""
Role Classification Agent
=========================
Uses an OpenAI LLM to classify the new hire's role into a standard category
and determine the resources they will need.

Categories
----------
Engineering · Marketing · Operations · Finance · Human Resources · Design ·
Sales · Legal · Executive

The agent writes ``role_type`` and ``required_resources`` to the shared state.
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

SYSTEM_PROMPT = """You are an HR classification specialist. Given a new hire's 
role title and department, classify them into exactly ONE of these categories:

  Engineering, Marketing, Operations, Finance, Human Resources, Design, Sales, Legal, Executive

Then list the internal tools and resources this person will need.

Respond ONLY with valid JSON in this exact format — no markdown, no explanation:
{
  "role_type": "<category>",
  "required_resources": ["tool1", "tool2", ...]
}

Resource examples by category:
- Engineering: GitHub, Jira, AWS Console, CI/CD Pipeline, VS Code License
- Marketing: HubSpot, Canva Pro, Google Analytics, Social Media Tools
- Operations: Monday.com, Slack, Notion, ERP System
- Finance: QuickBooks, SAP, Excel Advanced, Bloomberg Terminal
- Human Resources: BambooHR, Workday, ADP, LinkedIn Recruiter
- Design: Figma, Adobe Creative Suite, InVision, Miro
- Sales: Salesforce, HubSpot CRM, LinkedIn Sales Navigator, Gong
- Legal: Westlaw, DocuSign, Contract Management System
- Executive: Board Portal, Executive Dashboard, All-Access Badge
"""


# ── Agent Node ────────────────────────────────────────────────────────────────


def classify_role(state: OnboardingState) -> dict:
    """LangGraph node — classifies the employee role and required resources."""
    logger.info(
        "▶ Role Classification Agent — classifying %s (%s / %s)",
        state["employee_name"],
        state["role"],
        state["department"],
    )

    llm = ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        temperature=0,
    )

    human_msg = (
        f"New hire details:\n"
        f"  Name: {state['employee_name']}\n"
        f"  Role: {state['role']}\n"
        f"  Department: {state['department']}\n"
        f"  Employment Type: {state.get('employment_type', 'Full-time')}\n"
    )

    response = llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=human_msg),
    ])

    try:
        result = json.loads(response.content)
        role_type = result["role_type"]
        required_resources = result["required_resources"]
    except (json.JSONDecodeError, KeyError) as exc:
        logger.warning("LLM returned unparseable response, using fallback: %s", exc)
        role_type = "Operations"
        required_resources = ["Slack", "Notion", "Email"]

    logger.info(
        "✔ Role classified → %s | Resources: %s",
        role_type,
        ", ".join(required_resources),
    )

    return {
        "role_type": role_type,
        "required_resources": required_resources,
        "tasks_completed": state.get("tasks_completed", []) + ["Role Classification"],
    }
