"""YouTube Analytics API client wrapper.

Handles authentication and provides access to YouTube Analytics
for channel-level and video-level reporting.
"""

from __future__ import annotations

import logging

from googleapiclient.discovery import build

logger = logging.getLogger(__name__)


def get_analytics_client(credentials: object):
    """Get a YouTube Analytics API client.

    Args:
        credentials: Google OAuth credentials object (required -- analytics
                     is never available with just an API key).

    Returns:
        YouTube Analytics API resource object.
    """
    if isinstance(credentials, dict):
        from google.oauth2.credentials import Credentials
        credentials = Credentials(
            token=credentials.get("token"),
            refresh_token=credentials.get("refresh_token"),
            token_uri=credentials.get("token_uri"),
            client_id=credentials.get("client_id"),
            client_secret=credentials.get("client_secret"),
            scopes=credentials.get("scopes"),
        )
    return build("youtubeAnalytics", "v2", credentials=credentials)
