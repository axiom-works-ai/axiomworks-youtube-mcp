"""YouTube API quota tracking utility.

Tracks daily YouTube API quota usage against the 10,000 units/day limit.
Stores usage in SQLite at ~/.config/axiomworks-youtube-mcp/quota.db.

Quota costs (approximate):
- Search (search.list): 100 units
- Read (videos.list, channels.list, etc.): 1 unit
- Write (insert, update, delete): 50 units
- Upload (videos.insert, thumbnails.set): 1600 units
"""

from __future__ import annotations

import logging
import sqlite3
from datetime import date, datetime
from pathlib import Path

logger = logging.getLogger(__name__)

QUOTA_DB_PATH = Path.home() / ".config" / "axiomworks-youtube-mcp" / "quota.db"
DAILY_LIMIT = 10_000

# Pre-defined quota costs by operation type
QUOTA_COSTS = {
    "search": 100,
    "read": 1,
    "write": 50,
    "upload": 1600,
}


def _get_db() -> sqlite3.Connection:
    """Get or create the quota database connection."""
    QUOTA_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(QUOTA_DB_PATH))
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS quota_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            operation TEXT NOT NULL,
            units INTEGER NOT NULL,
            timestamp TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS daily_totals (
            date TEXT PRIMARY KEY,
            total_units INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    conn.commit()
    return conn


def reset_if_new_day() -> None:
    """Check if the current day has changed; daily_totals handles this
    automatically via date-keyed rows - no explicit reset needed.

    This function exists for explicit cache-clearing if desired.
    """
    # daily_totals uses date as key, so each new day starts fresh automatically
    pass


def track_usage(operation: str, units: int | None = None) -> dict:
    """Record a quota usage event.

    Args:
        operation: Type of operation - search, read, write, upload
        units: Explicit unit cost (overrides default for operation type)

    Returns:
        Dict with 'used_today', 'remaining', 'warning' (if applicable).
    """
    if units is None:
        units = QUOTA_COSTS.get(operation, 1)

    today = date.today().isoformat()
    now = datetime.now().isoformat()

    conn = _get_db()
    try:
        conn.execute(
            "INSERT INTO quota_usage (date, operation, units, timestamp) VALUES (?, ?, ?, ?)",
            (today, operation, units, now),
        )
        conn.execute(
            """
            INSERT INTO daily_totals (date, total_units) VALUES (?, ?)
            ON CONFLICT(date) DO UPDATE SET total_units = total_units + ?
            """,
            (today, units, units),
        )
        conn.commit()

        row = conn.execute(
            "SELECT total_units FROM daily_totals WHERE date = ?", (today,)
        ).fetchone()
        used_today = row[0] if row else units
    finally:
        conn.close()

    remaining = max(0, DAILY_LIMIT - used_today)
    result = {
        "used_today": used_today,
        "remaining": remaining,
        "daily_limit": DAILY_LIMIT,
    }

    if used_today >= DAILY_LIMIT:
        result["warning"] = (
            f"QUOTA EXCEEDED: {used_today}/{DAILY_LIMIT} units used today. "
            "API calls will be rejected by Google."
        )
    elif used_today >= DAILY_LIMIT * 0.8:
        result["warning"] = (
            f"QUOTA WARNING: {used_today}/{DAILY_LIMIT} units used today "
            f"({remaining} remaining). Consider rate-limiting requests."
        )

    return result


def get_remaining_quota() -> dict:
    """Get the current quota status without recording usage.

    Returns:
        Dict with 'used_today', 'remaining', 'daily_limit', and optional 'warning'.
    """
    today = date.today().isoformat()
    conn = _get_db()
    try:
        row = conn.execute(
            "SELECT total_units FROM daily_totals WHERE date = ?", (today,)
        ).fetchone()
        used_today = row[0] if row else 0
    finally:
        conn.close()

    remaining = max(0, DAILY_LIMIT - used_today)
    result = {
        "used_today": used_today,
        "remaining": remaining,
        "daily_limit": DAILY_LIMIT,
    }

    if used_today >= DAILY_LIMIT:
        result["warning"] = (
            f"QUOTA EXCEEDED: {used_today}/{DAILY_LIMIT} units used today."
        )
    elif used_today >= DAILY_LIMIT * 0.8:
        result["warning"] = (
            f"QUOTA WARNING: {used_today}/{DAILY_LIMIT} units used today "
            f"({remaining} remaining)."
        )

    return result


def check_quota_before_call(operation: str, units: int | None = None) -> None:
    """Check quota before making an API call. Raises if quota is exceeded.

    Args:
        operation: Type of operation - search, read, write, upload
        units: Explicit unit cost (overrides default)

    Raises:
        RuntimeError: If daily quota has been exceeded.
    """
    if units is None:
        units = QUOTA_COSTS.get(operation, 1)

    status = get_remaining_quota()
    if status["used_today"] >= DAILY_LIMIT:
        raise RuntimeError(
            f"YouTube API daily quota exceeded ({status['used_today']}/{DAILY_LIMIT} units). "
            "Quota resets at midnight Pacific Time. "
            "No API calls can be made until the quota resets."
        )
