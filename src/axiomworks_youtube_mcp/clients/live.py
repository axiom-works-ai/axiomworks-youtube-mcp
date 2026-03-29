"""YouTube Live Streaming API client wrapper.

Uses the YouTube Data API v3 liveBroadcasts and liveChatMessages resources.
The live streaming endpoints are part of the same v3 API, so we reuse the
same build call but keep a separate client instance for clarity.
"""

from __future__ import annotations

import logging

from googleapiclient.discovery import build

logger = logging.getLogger(__name__)


def get_live_client(credentials: object):
    """Get a YouTube Data API client configured for live streaming operations.

    Args:
        credentials: Google OAuth credentials object (required for all
                     live streaming operations).

    Returns:
        YouTube Data API resource object (same v3 service, separate instance).
    """
    return build("youtube", "v3", credentials=credentials)
