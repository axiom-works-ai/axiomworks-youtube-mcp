"""YouTube Music client wrapper using ytmusicapi.

Handles authentication and provides access to YouTube Music features:
search, library, playlists, history, charts, and more.
"""

from __future__ import annotations

import logging

from ytmusicapi import YTMusic

from ..config import YTMUSIC_OAUTH_PATH

logger = logging.getLogger(__name__)

# Cached client instances
_ytmusic_public: YTMusic | None = None
_ytmusic_authed: YTMusic | None = None


def get_ytmusic_client(require_auth: bool = False) -> YTMusic:
    """Get or create a YouTube Music client.

    Args:
        require_auth: If True, requires authenticated client (OAuth).
                     If False, returns public client (limited features).

    Returns:
        YTMusic client instance.
    """
    global _ytmusic_public, _ytmusic_authed

    if require_auth:
        if _ytmusic_authed is None:
            if not YTMUSIC_OAUTH_PATH.exists():
                raise ValueError(
                    "YouTube Music authentication required. "
                    "Run `axiomworks-youtube-mcp setup` to authenticate."
                )
            _ytmusic_authed = YTMusic(str(YTMUSIC_OAUTH_PATH))
            logger.info("YouTube Music authenticated client initialized")
        return _ytmusic_authed

    # Public client — no auth, limited to browsing/search
    if _ytmusic_public is None:
        _ytmusic_public = YTMusic()
        logger.info("YouTube Music public client initialized")
    return _ytmusic_public


def setup_ytmusic_oauth() -> bool:
    """Run the YouTube Music OAuth setup flow.

    Uses ytmusicapi's built-in OAuth flow (device code).

    Returns:
        True if setup succeeded.
    """
    try:
        YTMusic.setup_oauth(filepath=str(YTMUSIC_OAUTH_PATH), open_browser=True)
        logger.info(f"YouTube Music OAuth saved to {YTMUSIC_OAUTH_PATH}")
        return True
    except Exception as e:
        logger.error(f"YouTube Music OAuth setup failed: {e}")
        return False
