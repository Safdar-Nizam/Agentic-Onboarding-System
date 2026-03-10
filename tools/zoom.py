"""
Zoom Integration
================
Creates orientation meetings via the Zoom Server-to-Server OAuth API.

Setup
-----
1. Create a Server-to-Server OAuth app in the Zoom Marketplace.
2. Grant the ``meeting:write:admin`` scope.
3. Set ZOOM_ACCOUNT_ID, ZOOM_CLIENT_ID, and ZOOM_CLIENT_SECRET
   in your .env file.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

import requests

from config import settings

logger = logging.getLogger(__name__)

ZOOM_OAUTH_URL = "https://zoom.us/oauth/token"
ZOOM_API_BASE = "https://api.zoom.us/v2"


# ── Auth ──────────────────────────────────────────────────────────────────────


def _get_access_token() -> str:
    """Obtain a short-lived access token via Server-to-Server OAuth."""
    resp = requests.post(
        ZOOM_OAUTH_URL,
        params={"grant_type": "account_credentials", "account_id": settings.zoom_account_id},
        auth=(settings.zoom_client_id, settings.zoom_client_secret),
        timeout=15,
    )
    resp.raise_for_status()
    token: str = resp.json()["access_token"]
    logger.debug("Obtained Zoom access token.")
    return token


# ── Meeting ───────────────────────────────────────────────────────────────────


def create_meeting(
    topic: str,
    start_time: str | None = None,
    duration_minutes: int = 45,
    host_email: str = "me",
    agenda: str = "",
) -> dict[str, Any]:
    """Create a Zoom meeting and return the meeting details.

    Parameters
    ----------
    topic : str
        Meeting title shown to participants.
    start_time : str, optional
        ISO 8601 datetime string.  Defaults to tomorrow at 10:00 AM UTC.
    duration_minutes : int
        Meeting duration (default 45 min).
    host_email : str
        Zoom user email for the host.  ``"me"`` uses the authenticated user.
    agenda : str
        Optional meeting description / agenda text.

    Returns
    -------
    dict
        Zoom API response including ``join_url``, ``id``, ``start_time``, etc.
    """
    if start_time is None:
        start_dt = (datetime.utcnow() + timedelta(days=1)).replace(
            hour=10, minute=0, second=0, microsecond=0
        )
        start_time = start_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    token = _get_access_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    payload = {
        "topic": topic,
        "type": 2,  # scheduled meeting
        "start_time": start_time,
        "duration": duration_minutes,
        "timezone": "UTC",
        "agenda": agenda,
        "settings": {
            "host_video": True,
            "participant_video": True,
            "join_before_host": True,
            "waiting_room": False,
            "auto_recording": "none",
        },
    }

    url = f"{ZOOM_API_BASE}/users/{host_email}/meetings"
    resp = requests.post(url, json=payload, headers=headers, timeout=15)
    resp.raise_for_status()

    meeting: dict[str, Any] = resp.json()
    logger.info(
        "Zoom meeting created — ID: %s | Join: %s",
        meeting.get("id"),
        meeting.get("join_url"),
    )
    return meeting
