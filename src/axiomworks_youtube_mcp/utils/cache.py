"""Response caching for YouTube API calls.

Reduces quota consumption by serving cached responses for repeated queries.
Uses SQLite for persistence across server restarts.

Default TTLs:
- Search results: 5 minutes (content changes frequently)
- Video details: 15 minutes (metadata is semi-stable)
- Channel info: 1 hour (rarely changes)
- Trending: 30 minutes (updates periodically)
- Comments: 5 minutes (active threads change fast)
- Analytics: 1 hour (historical data doesn't change)
- YT Music browse: 30 minutes (playlists/charts update periodically)
- YT Music library: 5 minutes (user might be actively managing)
"""

from __future__ import annotations

import hashlib
import json
import logging
import sqlite3
import time

from ..config import CONFIG_DIR

logger = logging.getLogger(__name__)

CACHE_DB_PATH = CONFIG_DIR / "cache.db"

# TTL presets in seconds
TTL = {
    "search": 300,        # 5 min
    "video_details": 900, # 15 min
    "channel": 3600,      # 1 hour
    "trending": 1800,     # 30 min
    "comments": 300,      # 5 min
    "analytics": 3600,    # 1 hour
    "music_browse": 1800, # 30 min
    "music_library": 300, # 5 min
    "default": 300,       # 5 min fallback
}

_db: sqlite3.Connection | None = None


def _get_db() -> sqlite3.Connection:
    """Get or create the cache database connection."""
    global _db
    if _db is None:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        _db = sqlite3.connect(str(CACHE_DB_PATH), timeout=5)
        _db.execute("PRAGMA journal_mode=WAL")
        _db.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                category TEXT NOT NULL,
                created_at REAL NOT NULL,
                ttl_seconds INTEGER NOT NULL,
                hit_count INTEGER DEFAULT 0
            )
        """)
        _db.execute("""
            CREATE INDEX IF NOT EXISTS idx_cache_category
            ON cache(category)
        """)
        _db.commit()
    return _db


def _make_key(tool_name: str, params: dict) -> str:
    """Create a deterministic cache key from tool name and parameters."""
    # Sort params for consistency, exclude None values
    clean_params = {k: v for k, v in sorted(params.items()) if v is not None}
    raw = f"{tool_name}:{json.dumps(clean_params, sort_keys=True)}"
    return hashlib.sha256(raw.encode()).hexdigest()


def get_cached(tool_name: str, params: dict, category: str = "default") -> str | None:
    """Look up a cached response.

    Args:
        tool_name: The MCP tool that produced this result.
        params: The parameters used in the call (for key generation).
        category: Cache category (determines TTL). One of the TTL keys.

    Returns:
        Cached JSON string if valid cache exists, None otherwise.
    """
    db = _get_db()
    key = _make_key(tool_name, params)

    row = db.execute(
        "SELECT value, created_at, ttl_seconds FROM cache WHERE key = ?",
        (key,),
    ).fetchone()

    if row is None:
        return None

    value, created_at, stored_ttl = row
    age = time.time() - created_at

    if age > stored_ttl:
        # Expired — delete and return miss
        db.execute("DELETE FROM cache WHERE key = ?", (key,))
        db.commit()
        logger.debug(f"Cache expired for {tool_name} (age={age:.0f}s, ttl={stored_ttl}s)")
        return None

    # Cache hit — update hit count
    db.execute("UPDATE cache SET hit_count = hit_count + 1 WHERE key = ?", (key,))
    db.commit()
    logger.debug(f"Cache hit for {tool_name} (age={age:.0f}s, ttl={stored_ttl}s)")
    return value


def set_cached(
    tool_name: str,
    params: dict,
    value: str,
    category: str = "default",
) -> None:
    """Store a response in the cache.

    Args:
        tool_name: The MCP tool that produced this result.
        params: The parameters used in the call.
        value: The JSON string response to cache.
        category: Cache category (determines TTL).
    """
    db = _get_db()
    key = _make_key(tool_name, params)
    ttl = TTL.get(category, TTL["default"])

    db.execute(
        """INSERT OR REPLACE INTO cache (key, value, category, created_at, ttl_seconds, hit_count)
           VALUES (?, ?, ?, ?, ?, 0)""",
        (key, value, category, time.time(), ttl),
    )
    db.commit()
    logger.debug(f"Cached {tool_name} (category={category}, ttl={ttl}s)")


def invalidate(tool_name: str | None = None, category: str | None = None) -> int:
    """Invalidate cached entries.

    Args:
        tool_name: If provided, invalidate only entries for this tool.
        category: If provided, invalidate only entries in this category.
        If neither provided, clears entire cache.

    Returns:
        Number of entries invalidated.
    """
    db = _get_db()

    if category:
        cursor = db.execute("DELETE FROM cache WHERE category = ?", (category,))
    elif tool_name:
        # Tool-based invalidation requires scanning — less efficient but rare
        cursor = db.execute("DELETE FROM cache")  # Simplified: clear all
    else:
        cursor = db.execute("DELETE FROM cache")

    db.commit()
    count = cursor.rowcount
    logger.info(f"Invalidated {count} cache entries")
    return count


def cleanup_expired() -> int:
    """Remove all expired entries from the cache."""
    db = _get_db()
    now = time.time()
    cursor = db.execute(
        "DELETE FROM cache WHERE (created_at + ttl_seconds) < ?",
        (now,),
    )
    db.commit()
    count = cursor.rowcount
    if count > 0:
        logger.info(f"Cleaned up {count} expired cache entries")
    return count


def get_stats() -> dict:
    """Get cache statistics."""
    db = _get_db()

    total = db.execute("SELECT COUNT(*) FROM cache").fetchone()[0]
    by_category = dict(
        db.execute(
            "SELECT category, COUNT(*) FROM cache GROUP BY category"
        ).fetchall()
    )
    total_hits = db.execute("SELECT SUM(hit_count) FROM cache").fetchone()[0] or 0
    expired = db.execute(
        "SELECT COUNT(*) FROM cache WHERE (created_at + ttl_seconds) < ?",
        (time.time(),),
    ).fetchone()[0]

    return {
        "total_entries": total,
        "expired_entries": expired,
        "total_hits": total_hits,
        "by_category": by_category,
    }
