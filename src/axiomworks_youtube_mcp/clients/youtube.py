"""YouTube Data API v3 client wrapper.

Handles authentication, quota tracking, and provides a clean interface
to the Google API Python client.
"""

from __future__ import annotations

import asyncio
import json
import logging
import subprocess

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
        # OAuth — full access.
        # googleapiclient.build() needs a Credentials object, not a dict.
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
        return build("youtube", "v3", credentials=credentials)

    if api_key:
        # API key — read-only public access
        if _youtube_client is None:
            _youtube_client = build("youtube", "v3", developerKey=api_key)
        return _youtube_client

    raise ValueError("Either api_key or credentials must be provided.")


async def get_transcript_via_ytdlp(video_id: str, language: str = "en") -> str | None:
    """Extract transcript using yt-dlp (no auth needed).

    Downloads the actual subtitle file to a temp directory and extracts
    text — works for most videos without any API key or OAuth setup.
    """
    import tempfile
    import os
    import shutil

    # Find yt-dlp binary (may not be in PATH when running via uvx/venv)
    yt_dlp = shutil.which("yt-dlp")
    if not yt_dlp:
        # Try common locations
        import sys
        for prefix in [sys.prefix, os.path.dirname(sys.executable)]:
            candidate = os.path.join(prefix, "bin", "yt-dlp")
            if not os.path.isabs(prefix):
                candidate = os.path.join(os.path.dirname(sys.executable), "yt-dlp")
            if os.path.exists(candidate):
                yt_dlp = candidate
                break
    if not yt_dlp:
        yt_dlp = "yt-dlp"  # last resort


    url = f"https://www.youtube.com/watch?v={video_id}"

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            outfile = os.path.join(tmpdir, "sub")
            result = await asyncio.to_thread(
                subprocess.run,
                [
                    yt_dlp,
                    "--skip-download",
                    "--write-subs",
                    "--write-auto-subs",
                    "--sub-lang", language,
                    "--sub-format", "json3",
                    "--no-warnings",
                    "-o", outfile,
                    url,
                ],
                capture_output=True,
                text=True,
                timeout=60,
            )

            import glob
            sub_files = glob.glob(os.path.join(tmpdir, "sub.*.json3"))
            if not sub_files:
                sub_files = glob.glob(os.path.join(tmpdir, "sub.*.vtt"))
            if not sub_files:
                sub_files = glob.glob(os.path.join(tmpdir, "sub.*"))

            if sub_files:
                with open(sub_files[0]) as f:
                    raw = f.read()
                return _extract_text_from_subs(raw)

    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        logger.warning(f"yt-dlp transcript extraction failed: {e}")

    return None


def _extract_text_from_subs(raw: str) -> str:
    """Extract plain text from various subtitle formats."""
    try:
        data = json.loads(raw)
        if isinstance(data, dict) and "events" in data:
            texts = []
            for event in data["events"]:
                segs = event.get("segs", [])
                text = "".join(seg.get("utf8", "") for seg in segs).strip()
                if text and text != "\n":
                    texts.append(text)
            return " ".join(texts)
    except (json.JSONDecodeError, KeyError):
        pass

    # Try VTT/SRT: strip headers, timestamps, line numbers
    lines = raw.split("\n")
    texts = []
    for line in lines:
        line = line.strip()
        if (line and not line.startswith("WEBVTT") and not line.startswith("Kind:")
           and not line.startswith("Language:") and "-->" not in line
           and not line.isdigit() and not line.startswith("NOTE")):
            texts.append(line)
    if texts:
        return " ".join(texts)

    return raw[:10000]
