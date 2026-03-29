"""YouTube Data API v3 client wrapper.

Handles authentication, quota tracking, and provides a clean interface
to the Google API Python client.
"""

from __future__ import annotations

import asyncio
import json
import logging
import subprocess
from functools import lru_cache

from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

# Cache the client to avoid rebuilding on every call
_youtube_client = None


def get_youtube_client(
    api_key: str | None = None,
    credentials: object | None = None,
):
    """Get or create a YouTube Data API client.

    Args:
        api_key: YouTube Data API key (for public data)
        credentials: Google OAuth credentials object (for private data)

    Returns:
        YouTube API resource object.
    """
    global _youtube_client

    if credentials:
        # OAuth — full access
        return build("youtube", "v3", credentials=credentials)

    if api_key:
        # API key — read-only public access
        if _youtube_client is None:
            _youtube_client = build("youtube", "v3", developerKey=api_key)
        return _youtube_client

    raise ValueError("Either api_key or credentials must be provided.")


async def get_transcript_via_ytdlp(video_id: str, language: str = "en") -> str | None:
    """Extract transcript using yt-dlp (no auth needed).

    This is the primary transcript method — works for most videos
    without any API key or OAuth setup.
    """
    url = f"https://www.youtube.com/watch?v={video_id}"

    try:
        result = await asyncio.to_thread(
            subprocess.run,
            [
                "yt-dlp",
                "--skip-download",
                "--write-subs",
                "--write-auto-subs",
                "--sub-lang", language,
                "--sub-format", "json3",
                "--output", "-",
                "--print", "%(subtitles)j",
                url,
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0 and result.stdout.strip():
            # Try to parse subtitle data
            try:
                subs_data = json.loads(result.stdout)
                # Extract text from subtitle format
                if isinstance(subs_data, dict):
                    for lang_key, tracks in subs_data.items():
                        if isinstance(tracks, list) and tracks:
                            # Use first available track
                            track = tracks[0]
                            if "url" in track:
                                # Download the actual subtitle file
                                sub_result = await asyncio.to_thread(
                                    subprocess.run,
                                    ["yt-dlp", "--no-download", url,
                                     "--write-subs", "--write-auto-subs",
                                     "--sub-lang", language,
                                     "--print-to-file", "%(subtitles)j", "/dev/stdout"],
                                    capture_output=True, text=True, timeout=30,
                                )
                                if sub_result.stdout:
                                    return _extract_text_from_subs(sub_result.stdout)
            except json.JSONDecodeError:
                pass

            # Fallback: just return the raw output if it looks like text
            if len(result.stdout) > 50:
                return result.stdout[:10000]  # Cap at 10k chars

    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        logger.warning(f"yt-dlp transcript extraction failed: {e}")

    return None


def _extract_text_from_subs(raw: str) -> str:
    """Extract plain text from various subtitle formats."""
    try:
        data = json.loads(raw)
        if isinstance(data, dict) and "events" in data:
            # json3 format
            texts = []
            for event in data["events"]:
                segs = event.get("segs", [])
                for seg in segs:
                    text = seg.get("utf8", "").strip()
                    if text and text != "\n":
                        texts.append(text)
            return " ".join(texts)
    except (json.JSONDecodeError, KeyError):
        pass

    # Return raw if we can't parse
    return raw[:10000]
