"""
FastAPI Service Layer (Optional)
================================
Provides REST endpoints for triggering onboarding manually and checking
status — useful for integration with other internal systems or a frontend.

Usage
-----
    uvicorn api:app --reload --port 8000
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr, Field

from config import setup_logging
from workflow import run_onboarding
from db.database import get_employee, get_onboarding_tasks

# ── Logging ───────────────────────────────────────────────────────────────────
setup_logging()
logger = logging.getLogger(__name__)

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="AI Onboarding Agent API",
    description=(
        "REST interface for the AI New-Employee Onboarding Agent.  "
        "Trigger onboarding workflows and query status."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


# ── Schemas ───────────────────────────────────────────────────────────────────


class OnboardRequest(BaseModel):
    """Payload to manually trigger onboarding for a new hire."""

    employee_name: str = Field(..., min_length=1, examples=["Sarah Chen"])
    employee_email: EmailStr = Field(..., examples=["sarah.chen@example.com"])
    role: str = Field(..., min_length=1, examples=["Senior Software Engineer"])
    department: str = Field(..., min_length=1, examples=["Engineering"])
    start_date: str = Field(..., examples=["2026-03-15"])
    manager: str = Field(..., min_length=1, examples=["David Kim"])
    location: str = Field(default="Remote", examples=["San Francisco"])
    employment_type: str = Field(default="Full-time", examples=["Full-time"])


class OnboardResponse(BaseModel):
    """Summary returned after the onboarding workflow completes."""

    employee_id: str
    employee_name: str
    status: str
    tasks_completed: list[str]
    meeting_link: str
    assigned_laptop: str
    email_sent: bool
    errors: list[str]


class StatusResponse(BaseModel):
    """Employee onboarding status response."""

    employee_id: str
    name: str
    email: str
    role: str
    department: str
    status: str
    tasks: list[dict[str, Any]]


# ── Endpoints ─────────────────────────────────────────────────────────────────


@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint."""
    return {
        "service": "AI Onboarding Agent",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }


@app.post("/onboard", response_model=OnboardResponse, tags=["Onboarding"])
async def trigger_onboarding(payload: OnboardRequest):
    """Manually trigger the full onboarding workflow for a new employee."""
    logger.info("API — triggering onboarding for %s", payload.employee_name)

    try:
        result = run_onboarding(payload.model_dump())
        return OnboardResponse(
            employee_id=result.get("employee_id", ""),
            employee_name=result.get("employee_name", payload.employee_name),
            status=result.get("status", "Unknown"),
            tasks_completed=result.get("tasks_completed", []),
            meeting_link=result.get("meeting_link", ""),
            assigned_laptop=result.get("assigned_laptop", ""),
            email_sent=result.get("email_sent", False),
            errors=result.get("errors", []),
        )
    except Exception as exc:
        logger.error("Onboarding failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@app.get(
    "/status/{employee_id}",
    response_model=StatusResponse,
    tags=["Status"],
)
async def get_onboarding_status(employee_id: str):
    """Query the onboarding status and task list for an employee."""
    try:
        employee = get_employee(employee_id)
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")

        tasks = get_onboarding_tasks(employee_id)

        return StatusResponse(
            employee_id=employee["employee_id"],
            name=employee["name"],
            email=employee["email"],
            role=employee["role"],
            department=employee["department"],
            status=employee["status"],
            tasks=[dict(t) for t in tasks],
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Status query failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))
