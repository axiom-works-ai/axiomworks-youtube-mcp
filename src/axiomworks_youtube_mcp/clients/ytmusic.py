"""YouTube Music client wrapper using ytmusicapi.

Handles authentication and provides access to YouTube Music features:
search, library, playlists, history, charts, and more.
"""

from __future__ import annotations

import json
import logging

from ytmusicapi import YTMusic
from ytmusicapi.auth.oauth import OAuthCredentials

from ..config import YTMUSIC_OAUTH_PATH, YTMUSIC_BROWSER_PATH, CONFIG_DIR

logger = logging.getLogger(__name__)

# Cached client instances
_ytmusic_public: YTMusic | None = None
_ytmusic_authed: YTMusic | None = None


def _patch_refreshing_token():
    """Patch RefreshingToken to ignore unknown kwargs from Google's OAuth response."""
    from ytmusicapi.auth.oauth.token import RefreshingToken

    if not getattr(RefreshingToken, "_patched", False):
        _orig_init = RefreshingToken.__init__

        def _patched_init(self, *args, **kwargs):
            kwargs.pop("refresh_token_expires_in", None)
            return _orig_init(self, *args, **kwargs)

        RefreshingToken.__init__ = _patched_init
        RefreshingToken._patched = True


def _get_oauth_credentials() -> OAuthCredentials | None:
    """Build OAuthCredentials from client_secrets_tv.json for token refresh."""
    tv_path = CONFIG_DIR / "client_secrets_tv.json"
    if not tv_path.exists():
        return None
    try:
        with open(tv_path) as f:
            tv = json.load(f).get("installed", {})
        return OAuthCredentials(
            client_id=tv["client_id"],
            client_secret=tv["client_secret"],
        )
    except (KeyError, json.JSONDecodeError, OSError):
        return None


def get_ytmusic_client(require_auth: bool = False) -> YTMusic:
    """Get or create a YouTube Music client.

    Args:
        require_auth: If True, requires authenticated client (OAuth).
                     If False, returns public client (limited features).

    Returns:
        YTMusic client instance.
    """
    global _ytmusic_public, _ytmusic_authed

    _patch_refreshing_token()

    if require_auth:
        if _ytmusic_authed is None:
            # Prefer browser cookie auth (SAPISIDHASH) — required for library/history.
            # TV OAuth tokens lack user identity, so YT Music internal API returns 400.
            if YTMUSIC_BROWSER_PATH.exists():
                _ytmusic_authed = YTMusic(auth=str(YTMUSIC_BROWSER_PATH))
                logger.info("YouTube Music client initialized (browser cookie auth)")
            elif YTMUSIC_OAUTH_PATH.exists():
                _ytmusic_authed = YTMusic(
                    auth=str(YTMUSIC_OAUTH_PATH),
                    oauth_credentials=_get_oauth_credentials(),
                )
                logger.info("YouTube Music client initialized (OAuth — library tools may be limited)")
            else:
                raise ValueError(
                    "YouTube Music authentication required. "
                    "Run `axiomworks-youtube-mcp setup` to authenticate."
                )
        return _ytmusic_authed

    # Public client — no auth, limited to browsing/search
    if _ytmusic_public is None:
        _ytmusic_public = YTMusic()
        logger.info("YouTube Music public client initialized")
    return _ytmusic_public


def setup_ytmusic_oauth() -> bool:
    """Run the YouTube Music OAuth setup flow (TV/Limited Input device).

    Note: TV OAuth tokens lack user identity, so YT Music library/history
    endpoints return HTTP 400. For library access, use setup_ytmusic_browser()
    instead (browser cookie auth).

    Returns:
        True if setup succeeded.
    """
    try:
        from ytmusicapi import setup_oauth
        import os

        _patch_refreshing_token()

        tv_client_id = os.environ.get("YTMUSIC_CLIENT_ID", "")
        tv_client_secret = os.environ.get("YTMUSIC_CLIENT_SECRET", "")

        tv_secrets_path = CONFIG_DIR / "client_secrets_tv.json"
        if not tv_client_id and tv_secrets_path.exists():
            with open(tv_secrets_path) as f:
                tv_secrets = json.load(f)
            installed = tv_secrets.get("installed", {})
            tv_client_id = installed.get("client_id", "")
            tv_client_secret = installed.get("client_secret", "")

        if not tv_client_id or not tv_client_secret:
            logger.error(
                "YouTube Music OAuth requires a TV/Limited Input OAuth client.\n"
                "  1. Create one at: https://console.cloud.google.com/auth/clients\n"
                "     (Application type: TVs and Limited Input devices)\n"
                "  2. Save the JSON to: ~/.config/axiomworks-youtube-mcp/client_secrets_tv.json\n"
            )
            return False

        setup_oauth(
            filepath=str(YTMUSIC_OAUTH_PATH),
            client_id=tv_client_id,
            client_secret=tv_client_secret,
            open_browser=True,
        )
        logger.info(f"YouTube Music OAuth saved to {YTMUSIC_OAUTH_PATH}")
        return True
    except Exception as e:
        logger.error(f"YouTube Music OAuth setup failed: {e}")
        return False


def setup_ytmusic_browser() -> bool:
    """Run the YouTube Music browser cookie setup.

    Prompts user to paste request headers from Chrome DevTools.
    Browser auth (SAPISIDHASH) is required for library/history endpoints —
    TV OAuth tokens lack user identity and return HTTP 400.

    Returns:
        True if setup succeeded.
    """
    try:
        from ytmusicapi import setup

        setup(filepath=str(YTMUSIC_BROWSER_PATH))
        logger.info(f"YouTube Music browser auth saved to {YTMUSIC_BROWSER_PATH}")
        return True
    except Exception as e:
        logger.error(f"YouTube Music browser setup failed: {e}")
        return False
