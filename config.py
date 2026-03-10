"""
Configuration Module
====================
Centralised configuration loader for all environment variables.
Reads from a .env file and exposes typed settings via the Settings dataclass.
"""

import os
import logging
from dataclasses import dataclass, field
from dotenv import load_dotenv

# ── Load .env ────────────────────────────────────────────────────────────────
load_dotenv()

# ── Logging Setup ────────────────────────────────────────────────────────────
LOG_FORMAT = "%(asctime)s │ %(levelname)-8s │ %(name)-28s │ %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(level: str = "INFO") -> None:
    """Configure root logger with a consistent format."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format=LOG_FORMAT,
        datefmt=LOG_DATE_FORMAT,
    )


@dataclass(frozen=True)
class Settings:
    """Immutable application settings populated from environment variables."""

    # ── OpenAI ────────────────────────────────────────────────────────────
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    openai_model: str = field(default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-4o-mini"))

    # ── Google Sheets ─────────────────────────────────────────────────────
    google_sheets_id: str = field(
        default_factory=lambda: os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID", "")
    )
    google_sheets_range: str = field(
        default_factory=lambda: os.getenv("GOOGLE_SHEETS_RANGE", "Sheet1!A:J")
    )
    google_service_account_file: str = field(
        default_factory=lambda: os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "service_account.json")
    )

    # ── Gmail ─────────────────────────────────────────────────────────────
    gmail_sender_email: str = field(
        default_factory=lambda: os.getenv("GMAIL_SENDER_EMAIL", "")
    )
    gmail_credentials_file: str = field(
        default_factory=lambda: os.getenv("GMAIL_CREDENTIALS_FILE", "credentials.json")
    )
    gmail_token_file: str = field(
        default_factory=lambda: os.getenv("GMAIL_TOKEN_FILE", "token.json")
    )

    # ── Zoom ──────────────────────────────────────────────────────────────
    zoom_account_id: str = field(default_factory=lambda: os.getenv("ZOOM_ACCOUNT_ID", ""))
    zoom_client_id: str = field(default_factory=lambda: os.getenv("ZOOM_CLIENT_ID", ""))
    zoom_client_secret: str = field(default_factory=lambda: os.getenv("ZOOM_CLIENT_SECRET", ""))

    # ── PostgreSQL ────────────────────────────────────────────────────────
    database_url: str = field(default_factory=lambda: os.getenv("DATABASE_URL", ""))
    db_host: str = field(default_factory=lambda: os.getenv("DB_HOST", "localhost"))
    db_port: int = field(default_factory=lambda: int(os.getenv("DB_PORT", "5432")))
    db_name: str = field(default_factory=lambda: os.getenv("DB_NAME", "onboarding_db"))
    db_user: str = field(default_factory=lambda: os.getenv("DB_USER", "postgres"))
    db_password: str = field(default_factory=lambda: os.getenv("DB_PASSWORD", ""))

    # ── Polling ───────────────────────────────────────────────────────────
    poll_interval: int = field(
        default_factory=lambda: int(os.getenv("POLL_INTERVAL_SECONDS", "30"))
    )


# ── Singleton ─────────────────────────────────────────────────────────────────
settings = Settings()
