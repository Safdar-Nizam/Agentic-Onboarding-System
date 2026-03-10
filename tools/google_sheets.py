"""
Google Sheets Integration
=========================
Uses the Google Sheets API v4 (via a service-account) to:
  • Poll the "New Hire Intake Sheet" for unprocessed rows.
  • Write onboarding status back to the sheet.

Setup
-----
1. Create a GCP project and enable the Google Sheets API.
2. Create a service-account and download the JSON key file.
3. Share the Google Sheet with the service-account email.
4. Set GOOGLE_SERVICE_ACCOUNT_FILE and GOOGLE_SHEETS_SPREADSHEET_ID
   in your .env file.
"""

from __future__ import annotations

import logging
from typing import Any

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from config import settings

logger = logging.getLogger(__name__)

# ── Scopes ────────────────────────────────────────────────────────────────────
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# ── Expected column order in the intake sheet ─────────────────────────────────
COLUMNS = [
    "employee_name",
    "employee_email",
    "role",
    "department",
    "start_date",
    "manager",
    "location",
    "employment_type",
    "onboarding_status",   # written back by the agent
    "processed",           # flag to skip already-handled rows
]


def _get_sheets_service():
    """Authenticate and return a Sheets API service object."""
    creds = Credentials.from_service_account_file(
        settings.google_service_account_file,
        scopes=SCOPES,
    )
    service = build("sheets", "v4", credentials=creds, cache_discovery=False)
    return service.spreadsheets()


# ── Read ──────────────────────────────────────────────────────────────────────


def get_new_hires() -> list[dict[str, str]]:
    """Return rows from the intake sheet that have NOT yet been processed.

    Each row is returned as a dict keyed by COLUMNS. A row is "new" when
    the 'processed' column (J) is empty or missing.
    """
    try:
        sheets = _get_sheets_service()
        result = (
            sheets.values()
            .get(
                spreadsheetId=settings.google_sheets_id,
                range=settings.google_sheets_range,
            )
            .execute()
        )
        rows: list[list[str]] = result.get("values", [])

        if not rows:
            logger.info("Sheet is empty — no new hires detected.")
            return []

        # First row is the header — skip it
        data_rows = rows[1:]
        new_hires: list[dict[str, str]] = []

        for idx, row in enumerate(data_rows, start=2):  # row 2 in sheet
            # Pad short rows so zip doesn't drop columns
            padded = row + [""] * (len(COLUMNS) - len(row))
            record = dict(zip(COLUMNS, padded))

            # Skip already-processed rows
            if record.get("processed", "").strip().upper() == "YES":
                continue

            record["_sheet_row"] = str(idx)  # keep row number for updates
            new_hires.append(record)

        logger.info("Found %d new hire(s) to process.", len(new_hires))
        return new_hires

    except HttpError as exc:
        logger.error("Google Sheets API error: %s", exc)
        raise


# ── Write ─────────────────────────────────────────────────────────────────────


def update_sheet_status(
    row_number: int,
    status: str,
    mark_processed: bool = True,
) -> None:
    """Write onboarding status and 'processed' flag back to the sheet.

    Parameters
    ----------
    row_number : int
        1-indexed row in the sheet (row 1 = header).
    status : str
        e.g. "Completed", "In Progress", "Failed".
    mark_processed : bool
        If True, writes "YES" in the processed column.
    """
    try:
        sheets = _get_sheets_service()

        # Column I = Onboarding Status, Column J = Processed
        range_str = f"Sheet1!I{row_number}:J{row_number}"
        body: dict[str, Any] = {
            "values": [[status, "YES" if mark_processed else ""]],
        }

        sheets.values().update(
            spreadsheetId=settings.google_sheets_id,
            range=range_str,
            valueInputOption="USER_ENTERED",
            body=body,
        ).execute()

        logger.info("Updated Sheet row %d → status=%s", row_number, status)

    except HttpError as exc:
        logger.error("Failed to update Sheet row %d: %s", row_number, exc)
        raise
