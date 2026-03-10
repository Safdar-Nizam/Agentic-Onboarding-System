"""
Gmail Integration
=================
Sends onboarding emails through the Gmail API using OAuth 2.0 credentials.

Setup
-----
1. Create OAuth 2.0 Client ID credentials in your GCP project
   (Desktop application type).
2. Download the JSON file → ``credentials.json``.
3. On first run the module opens a browser for consent; after that
   the refresh-token is cached in ``token.json``.
4. Set GMAIL_CREDENTIALS_FILE, GMAIL_TOKEN_FILE, and GMAIL_SENDER_EMAIL
   in your .env file.
"""

from __future__ import annotations

import base64
import logging
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from config import settings

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


def _get_gmail_service():
    """Authenticate and return a Gmail API service object."""
    creds = None

    # Load cached token
    if os.path.exists(settings.gmail_token_file):
        creds = Credentials.from_authorized_user_file(
            settings.gmail_token_file, SCOPES
        )

    # Refresh or run interactive flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                settings.gmail_credentials_file, SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Save for next run
        with open(settings.gmail_token_file, "w") as token_fh:
            token_fh.write(creds.to_json())

    return build("gmail", "v1", credentials=creds, cache_discovery=False)


# ── Send ──────────────────────────────────────────────────────────────────────


def send_welcome_email(
    to: str,
    subject: str,
    body_html: str,
) -> dict:
    """Compose and send an HTML email via the Gmail API.

    Parameters
    ----------
    to : str
        Recipient email address.
    subject : str
        Email subject line.
    body_html : str
        HTML body content (LLM-generated welcome message).

    Returns
    -------
    dict
        Gmail API response containing the message ``id`` and ``threadId``.

    Raises
    ------
    HttpError
        If the Gmail API returns an error.
    """
    try:
        service = _get_gmail_service()

        message = MIMEMultipart("alternative")
        message["To"] = to
        message["From"] = settings.gmail_sender_email
        message["Subject"] = subject

        # Plain-text fallback
        plain_text = body_html.replace("<br>", "\n").replace("</p>", "\n")
        message.attach(MIMEText(plain_text, "plain"))
        message.attach(MIMEText(body_html, "html"))

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
        result = (
            service.users()
            .messages()
            .send(userId="me", body={"raw": raw})
            .execute()
        )

        logger.info(
            "Welcome email sent to %s  (message id: %s)",
            to, result.get("id"),
        )
        return result

    except HttpError as exc:
        logger.error("Gmail API error sending to %s: %s", to, exc)
        raise
