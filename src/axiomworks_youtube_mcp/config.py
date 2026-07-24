"""Configuration management for the YouTube MCP server.

Handles API keys, OAuth tokens, and server settings.
Config is stored in ~/.config/axiomworks-youtube-mcp/
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class AuthTier(Enum):
    """Authentication tiers determine which tools are available.

    Tier 0: Zero config — transcripts via yt-dlp, YouTube Music browsing
    Tier 1: API key — YouTube search, details, comments read, trending
    Tier 2: OAuth — Everything: writes, analytics, library, playlists
    """

    ZERO = 0
    API_KEY = 1
    OAUTH = 2


CONFIG_DIR = Path.home() / ".config" / "axiomworks-youtube-mcp"
GOOGLE_OAUTH_PATH = CONFIG_DIR / "google-oauth.json"
YTMUSIC_OAUTH_PATH = CONFIG_DIR / "ytmusic-oauth.json"
API_KEY_PATH = CONFIG_DIR / "api-key.txt"
CACHE_DB_PATH = CONFIG_DIR / "cache.db"


@dataclass
class ServerConfig:
    """Server configuration loaded from disk."""

    api_key: str | None = None
    google_oauth_credentials: dict | None = None
    ytmusic_auth_path: Path | None = None
    cache_enabled: bool = True
    cache_ttl_seconds: int = 300  # 5 minutes
    quota_daily_limit: int = 10_000  # YouTube API quota
    quota_used_today: int = 0

    @property
    def auth_tier(self) -> AuthTier:
        """Determine the current authentication tier."""
        if self.google_oauth_credentials or self.ytmusic_auth_path:
            return AuthTier.OAUTH
        if self.api_key:
            return AuthTier.API_KEY
        return AuthTier.ZERO

    @property
    def available_tool_count(self) -> int:
        """Estimate available tools based on auth tier."""
        match self.auth_tier:
            case AuthTier.ZERO:
                return 14  # Transcripts + YT Music browsing
            case AuthTier.API_KEY:
                return 31  # + YouTube read operations
            case AuthTier.OAUTH:
                return 68  # Everything


def ensure_config_dir() -> Path:
    """Create config directory if it doesn't exist."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    return CONFIG_DIR


def load_config() -> ServerConfig:
    """Load configuration from disk."""
    config = ServerConfig()

    # Load API key
    if API_KEY_PATH.exists():
        key = API_KEY_PATH.read_text().strip()
        if key:
            config.api_key = key

    # Load Google OAuth credentials
    if GOOGLE_OAUTH_PATH.exists():
        try:
            config.google_oauth_credentials = json.loads(GOOGLE_OAUTH_PATH.read_text())
        except (json.JSONDecodeError, OSError):
            pass

    # Load YouTube Music auth
    if YTMUSIC_OAUTH_PATH.exists():
        config.ytmusic_auth_path = YTMUSIC_OAUTH_PATH

    return config


def save_api_key(key: str) -> None:
    """Save API key to disk."""
    ensure_config_dir()
    API_KEY_PATH.write_text(key)
    API_KEY_PATH.chmod(0o600)


def save_google_oauth(credentials: dict) -> None:
    """Save Google OAuth credentials to disk."""
    ensure_config_dir()
    GOOGLE_OAUTH_PATH.write_text(json.dumps(credentials, indent=2))
    GOOGLE_OAUTH_PATH.chmod(0o600)
