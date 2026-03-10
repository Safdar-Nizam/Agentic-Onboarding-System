"""
Database Helper Module
======================
Provides connection pooling and CRUD helpers for the onboarding database.
All functions use context managers so callers never need to worry about
closing connections or cursors.
"""

from __future__ import annotations

import logging
import uuid
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Generator, Optional

import psycopg2
import psycopg2.extras

from config import settings

logger = logging.getLogger(__name__)

# ── Connection ────────────────────────────────────────────────────────────────


@contextmanager
def get_connection() -> Generator:
    """Yield a psycopg2 connection that auto-commits on success and rolls back
    on failure.  Always closes the connection when done."""
    conn = psycopg2.connect(
        host=settings.db_host,
        port=settings.db_port,
        dbname=settings.db_name,
        user=settings.db_user,
        password=settings.db_password,
    )
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


@contextmanager
def get_cursor(conn) -> Generator:
    """Yield a RealDictCursor from an existing connection."""
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        yield cur
    finally:
        cur.close()


# ── Employee CRUD ─────────────────────────────────────────────────────────────


def generate_employee_id() -> str:
    """Generate a unique employee ID like EMP-a1b2c3d4."""
    short = uuid.uuid4().hex[:8].upper()
    return f"EMP-{short}"


def insert_employee(
    name: str,
    email: str,
    role: str,
    department: str,
    start_date: str,
    manager: str,
    location: str = "Remote",
    employment_type: str = "Full-time",
) -> str:
    """Insert a new employee record and return the generated employee_id."""
    employee_id = generate_employee_id()
    sql = """
        INSERT INTO employees
            (employee_id, name, email, role, department, start_date,
             manager, location, employment_type, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'In Progress')
        ON CONFLICT (email) DO UPDATE SET status = 'In Progress'
        RETURNING employee_id;
    """
    with get_connection() as conn, get_cursor(conn) as cur:
        cur.execute(
            sql,
            (employee_id, name, email, role, department, start_date,
             manager, location, employment_type),
        )
        row = cur.fetchone()
        result_id = row["employee_id"] if row else employee_id
        logger.info("Inserted/updated employee %s (%s)", result_id, email)
        return result_id


def update_employee_status(employee_id: str, status: str) -> None:
    """Update the status column for an employee."""
    sql = "UPDATE employees SET status = %s, updated_at = NOW() WHERE employee_id = %s;"
    with get_connection() as conn, get_cursor(conn) as cur:
        cur.execute(sql, (status, employee_id))
        logger.info("Employee %s status → %s", employee_id, status)


def get_employee(employee_id: str) -> Optional[dict[str, Any]]:
    """Fetch a single employee record by ID."""
    sql = "SELECT * FROM employees WHERE employee_id = %s;"
    with get_connection() as conn, get_cursor(conn) as cur:
        cur.execute(sql, (employee_id,))
        return cur.fetchone()


# ── Onboarding Tasks ─────────────────────────────────────────────────────────


def insert_onboarding_task(employee_id: str, task_name: str) -> int:
    """Create a new onboarding task. Returns the task_id."""
    sql = """
        INSERT INTO onboarding_tasks (employee_id, task_name, task_status)
        VALUES (%s, %s, 'Pending')
        RETURNING task_id;
    """
    with get_connection() as conn, get_cursor(conn) as cur:
        cur.execute(sql, (employee_id, task_name))
        task_id: int = cur.fetchone()["task_id"]
        logger.info("Created task %s for employee %s: %s", task_id, employee_id, task_name)
        return task_id


def update_task_status(employee_id: str, task_name: str, status: str) -> None:
    """Mark an onboarding task as Completed / Failed / In Progress."""
    completed_at = datetime.utcnow() if status == "Completed" else None
    sql = """
        UPDATE onboarding_tasks
        SET task_status = %s, completed_at = %s
        WHERE employee_id = %s AND task_name = %s;
    """
    with get_connection() as conn, get_cursor(conn) as cur:
        cur.execute(sql, (status, completed_at, employee_id, task_name))
        logger.info("Task '%s' for %s → %s", task_name, employee_id, status)


def get_onboarding_tasks(employee_id: str) -> list[dict[str, Any]]:
    """Return all onboarding tasks for an employee."""
    sql = "SELECT * FROM onboarding_tasks WHERE employee_id = %s ORDER BY task_id;"
    with get_connection() as conn, get_cursor(conn) as cur:
        cur.execute(sql, (employee_id,))
        return cur.fetchall()


# ── Laptop Inventory ─────────────────────────────────────────────────────────


def assign_laptop(employee_id: str) -> Optional[str]:
    """Assign the first available laptop and return its ID, or None if empty."""
    sql = """
        UPDATE laptop_inventory
        SET status = 'Assigned', assigned_to = %s, assigned_at = NOW()
        WHERE laptop_id = (
            SELECT laptop_id FROM laptop_inventory
            WHERE status = 'Available'
            ORDER BY laptop_id
            LIMIT 1
            FOR UPDATE SKIP LOCKED
        )
        RETURNING laptop_id, model;
    """
    with get_connection() as conn, get_cursor(conn) as cur:
        cur.execute(sql, (employee_id,))
        row = cur.fetchone()
        if row:
            logger.info(
                "Assigned laptop %s (%s) to %s",
                row["laptop_id"], row["model"], employee_id,
            )
            return row["laptop_id"]
        logger.warning("No available laptops for %s", employee_id)
        return None


def get_available_laptops() -> list[dict[str, Any]]:
    """Return all laptops currently available."""
    sql = "SELECT * FROM laptop_inventory WHERE status = 'Available' ORDER BY laptop_id;"
    with get_connection() as conn, get_cursor(conn) as cur:
        cur.execute(sql, ())
        return cur.fetchall()
