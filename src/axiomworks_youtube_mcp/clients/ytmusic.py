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

    Uses ytmusicapi's OAuth with a TV/Limited Input device client
    (required by ytmusicapi's device code flow).

    Includes a workaround for ytmusicapi bug where Google's OAuth response
    includes 'refresh_token_expires_in' which RefreshingToken doesn't accept.

    Returns:
        True if setup succeeded.
    """
    try:
        from ytmusicapi import setup_oauth

        import json
        import os

        from ..config import CONFIG_DIR

        _patch_refreshing_token()

        # Read TV/Limited Input client credentials from config or env
        # ytmusicapi requires a TV-type OAuth client for its device code flow
        tv_client_id = os.environ.get("YTMUSIC_CLIENT_ID", "")
        tv_client_secret = os.environ.get("YTMUSIC_CLIENT_SECRET", "")

        # Fall back to client_secrets_tv.json
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
                "     Or set YTMUSIC_CLIENT_ID and YTMUSIC_CLIENT_SECRET env vars."
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
