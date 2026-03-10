"""
Main Entry Point
=================
Continuously polls the Google Sheet for new hires and launches the
LangGraph onboarding workflow for each one.

Usage
-----
    python main.py              # start polling (default 30s interval)
    python main.py --once       # process current new hires and exit
    python main.py --demo       # run a single demo employee (no APIs needed)
"""

from __future__ import annotations

import argparse
import logging
import sys
import time

from config import setup_logging, settings
from workflow import run_onboarding

logger = logging.getLogger(__name__)


# ── Demo Mode ─────────────────────────────────────────────────────────────────

def _demo_employee() -> dict:
    """Build the demo employee record, routing email to the configured sender
    so the welcome email lands in a real inbox during demo mode."""
    # Use the configured sender email so the test email is actually receivable
    demo_email = settings.gmail_sender_email or "sarah.chen@example.com"
    return {
        "employee_name": "Sarah Chen",
        "employee_email": demo_email,
        "role": "Senior Software Engineer",
        "department": "Engineering",
        "start_date": "2026-03-15",
        "manager": "David Kim",
        "location": "San Francisco",
        "employment_type": "Full-time",
    }


def run_demo() -> None:
    """Run the workflow with a demo employee — sends all real API calls
    (OpenAI, Zoom, Gmail, Supabase) using a sample employee record."""
    logger.info("🧪 Running in DEMO mode with sample employee data …")
    logger.info("   Email will be sent to your configured GMAIL_SENDER_EMAIL")

    result = run_onboarding(_demo_employee())

    logger.info("\n🏁 Demo complete.  Final status: %s", result.get("status", "Unknown"))
    if result.get("errors"):
        logger.info("   Errors (expected in demo mode):")
        for err in result["errors"]:
            logger.info("     ⚠ %s", err)


# ── Polling Mode ──────────────────────────────────────────────────────────────


def poll_for_new_hires(once: bool = False) -> None:
    """Continuously poll Google Sheets for new-hire rows.

    Parameters
    ----------
    once : bool
        If True, process all current new hires and exit.
    """
    from tools.google_sheets import get_new_hires

    logger.info(
        "📋 Starting Google Sheets poller (interval=%ds) …",
        settings.poll_interval,
    )

    while True:
        try:
            new_hires = get_new_hires()

            if not new_hires:
                logger.info("No new hires found.  Waiting …")
            else:
                for hire in new_hires:
                    logger.info(
                        "🆕 New hire detected — %s (%s)",
                        hire.get("employee_name"),
                        hire.get("employee_email"),
                    )
                    try:
                        run_onboarding(hire)
                    except Exception as exc:
                        logger.error(
                            "✖ Onboarding failed for %s: %s",
                            hire.get("employee_name"), exc,
                            exc_info=True,
                        )

        except KeyboardInterrupt:
            logger.info("⏹  Poller stopped by user.")
            break
        except Exception as exc:
            logger.error("✖ Polling error: %s", exc, exc_info=True)

        if once:
            logger.info("--once flag set.  Exiting after this cycle.")
            break

        time.sleep(settings.poll_interval)


# ── CLI ───────────────────────────────────────────────────────────────────────


def main() -> None:
    """Parse CLI arguments and launch the appropriate mode."""
    parser = argparse.ArgumentParser(
        description="AI New-Employee Onboarding Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python main.py              # continuous polling\n"
            "  python main.py --once       # one-shot processing\n"
            "  python main.py --demo       # demo with sample data\n"
        ),
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Process current new hires and exit immediately.",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run a demo workflow with sample employee data (no real API calls).",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Set logging level (default: INFO).",
    )
    args = parser.parse_args()

    setup_logging(args.log_level)

    logger.info("=" * 60)
    logger.info("  🤖  AI New-Employee Onboarding Agent  v1.0.0")
    logger.info("=" * 60)

    if args.demo:
        run_demo()
    else:
        poll_for_new_hires(once=args.once)


if __name__ == "__main__":
    main()
