"""MCP Server definition and tool registration.

This is the main entry point for the MCP server. It registers all tools
organized by group and handles the server lifecycle.
"""

from __future__ import annotations

import logging
from mcp.server.fastmcp import FastMCP

from .config import load_config, ServerConfig, AuthTier

logger = logging.getLogger(__name__)

# Create the MCP server instance
mcp = FastMCP(
    "axiomworks-youtube-mcp",
    version="0.1.0",
    description=(
        "The definitive YouTube + YouTube Music MCP server by Axiom Works. "
        "68 tools for search, playlists, comments, analytics, live streaming, "
        "and full YouTube Music library management."
    ),
)

# Load config at module level — tools check auth tier at call time
_config: ServerConfig | None = None


def get_config() -> ServerConfig:
    """Get or load the server configuration."""
    global _config
    if _config is None:
        _config = load_config()
    return _config


def require_api_key() -> str:
    """Get API key or raise a helpful error."""
    config = get_config()
    if not config.api_key:
        raise ValueError(
            "YouTube API key required. Run `axiomworks-youtube-mcp setup` "
            "or set YOUTUBE_API_KEY environment variable."
        )
    return config.api_key


def require_oauth() -> dict:
    """Get OAuth credentials or raise a helpful error."""
    config = get_config()
    if not config.google_oauth_credentials:
        raise ValueError(
            "Google OAuth required for this operation. "
            "Run `axiomworks-youtube-mcp setup` to authenticate."
        )
    return config.google_oauth_credentials


# ─── Group 1: YouTube Search & Discovery (API key sufficient) ───────────────


@mcp.tool()
async def youtube_search(
    query: str,
    type: str = "video",
    max_results: int = 10,
    order: str = "relevance",
    published_after: str | None = None,
    published_before: str | None = None,
    region_code: str | None = None,
    language: str | None = None,
) -> str:
    """Search YouTube for videos, channels, or playlists.

    Args:
        query: Search query string
        type: Type of result — video, channel, or playlist
        max_results: Number of results (1-50, default 10)
        order: Sort order — relevance, date, rating, viewCount, title
        published_after: ISO 8601 date filter (e.g., 2026-01-01T00:00:00Z)
        published_before: ISO 8601 date filter
        region_code: ISO 3166-1 alpha-2 country code (e.g., US)
        language: ISO 639-1 language code (e.g., en)

    Returns:
        JSON array of search results with video/channel/playlist details.
    """
    from .clients.youtube import get_youtube_client

    api_key = require_api_key()
    youtube = get_youtube_client(api_key=api_key)

    params: dict = {
        "part": "snippet",
        "q": query,
        "type": type,
        "maxResults": min(max_results, 50),
        "order": order,
    }
    if published_after:
        params["publishedAfter"] = published_after
    if published_before:
        params["publishedBefore"] = published_before
    if region_code:
        params["regionCode"] = region_code
    if language:
        params["relevanceLanguage"] = language

    response = youtube.search().list(**params).execute()
    return _format_search_results(response)


@mcp.tool()
async def youtube_trending(
    region_code: str = "US",
    category_id: str | None = None,
    max_results: int = 10,
) -> str:
    """Get trending videos for a region and optional category.

    Args:
        region_code: ISO 3166-1 alpha-2 country code (default: US)
        category_id: Video category ID (e.g., 10 for Music, 20 for Gaming)
        max_results: Number of results (1-50, default 10)

    Returns:
        JSON array of trending videos with statistics.
    """
    from .clients.youtube import get_youtube_client

    api_key = require_api_key()
    youtube = get_youtube_client(api_key=api_key)

    params: dict = {
        "part": "snippet,statistics,contentDetails",
        "chart": "mostPopular",
        "regionCode": region_code,
        "maxResults": min(max_results, 50),
    }
    if category_id:
        params["videoCategoryId"] = category_id

    response = youtube.videos().list(**params).execute()
    return _format_video_results(response)


@mcp.tool()
async def youtube_video_details(
    video_ids: str,
) -> str:
    """Get detailed metadata for one or more videos.

    Args:
        video_ids: Comma-separated video IDs (up to 50)

    Returns:
        JSON array with full video details: title, description, statistics,
        duration, tags, category, thumbnails, and publishing info.
    """
    from .clients.youtube import get_youtube_client

    api_key = require_api_key()
    youtube = get_youtube_client(api_key=api_key)

    response = (
        youtube.videos()
        .list(
            part="snippet,contentDetails,statistics,status,topicDetails",
            id=video_ids,
        )
        .execute()
    )
    return _format_video_results(response)


@mcp.tool()
async def youtube_video_transcript(
    video_id: str,
    language: str = "en",
) -> str:
    """Get captions/transcript for a video.

    Uses yt-dlp as primary method (no auth needed), falls back to
    YouTube Captions API if OAuth is available.

    Args:
        video_id: YouTube video ID
        language: Language code (default: en)

    Returns:
        Full transcript text, or error if no captions available.
    """
    from .clients.youtube import get_transcript_via_ytdlp

    # Try yt-dlp first (no auth needed, works for most videos)
    transcript = await get_transcript_via_ytdlp(video_id, language)
    if transcript:
        return transcript

    return f"No transcript available for video {video_id} in language '{language}'."


# ─── Group 2: Channel Operations ────────────────────────────────────────────


@mcp.tool()
async def youtube_channel_details(
    channel_id: str | None = None,
    username: str | None = None,
    handle: str | None = None,
) -> str:
    """Get channel information including stats, branding, and description.

    Provide one of: channel_id, username, or handle (e.g., @mkbhd).

    Args:
        channel_id: YouTube channel ID
        username: Legacy YouTube username
        handle: YouTube handle (e.g., @mkbhd)

    Returns:
        Channel details with subscriber count, video count, description, etc.
    """
    from .clients.youtube import get_youtube_client

    api_key = require_api_key()
    youtube = get_youtube_client(api_key=api_key)

    params: dict = {"part": "snippet,statistics,brandingSettings,contentDetails"}
    if channel_id:
        params["id"] = channel_id
    elif username:
        params["forUsername"] = username
    elif handle:
        params["forHandle"] = handle
    else:
        raise ValueError("Provide one of: channel_id, username, or handle")

    response = youtube.channels().list(**params).execute()
    return _format_channel_results(response)


# ─── Group 8: YouTube Music Search & Browse ─────────────────────────────────


@mcp.tool()
async def ytmusic_search(
    query: str,
    filter: str | None = None,
    limit: int = 20,
) -> str:
    """Search YouTube Music for songs, albums, artists, playlists, or videos.

    Args:
        query: Search query
        filter: Optional filter — songs, videos, albums, artists, playlists,
                community_playlists, featured_playlists, uploads
        limit: Max results (default 20)

    Returns:
        JSON array of search results with type-specific metadata.
    """
    from .clients.ytmusic import get_ytmusic_client

    ytmusic = get_ytmusic_client()
    results = ytmusic.search(query, filter=filter, limit=limit)
    return _format_ytmusic_results(results)


@mcp.tool()
async def ytmusic_get_artist(channel_id: str) -> str:
    """Get an artist's page: bio, top songs, albums, singles, videos, related.

    Args:
        channel_id: YouTube Music artist channel ID

    Returns:
        Artist details with discography, top songs, and related artists.
    """
    from .clients.ytmusic import get_ytmusic_client

    ytmusic = get_ytmusic_client()
    return _format_json(ytmusic.get_artist(channel_id))


@mcp.tool()
async def ytmusic_get_album(browse_id: str) -> str:
    """Get album details and full track listing.

    Args:
        browse_id: YouTube Music album browse ID

    Returns:
        Album metadata with track list, duration, and artists.
    """
    from .clients.ytmusic import get_ytmusic_client

    ytmusic = get_ytmusic_client()
    return _format_json(ytmusic.get_album(browse_id))


@mcp.tool()
async def ytmusic_get_song(video_id: str) -> str:
    """Get full metadata for a song.

    Args:
        video_id: YouTube Music video/song ID

    Returns:
        Song details including album, artists, duration, and playability.
    """
    from .clients.ytmusic import get_ytmusic_client

    ytmusic = get_ytmusic_client()
    return _format_json(ytmusic.get_song(video_id))


@mcp.tool()
async def ytmusic_get_lyrics(browse_id: str) -> str:
    """Get lyrics for a song.

    The browse_id comes from the watch playlist response (get_watch_playlist).

    Args:
        browse_id: Lyrics browse ID from watch playlist

    Returns:
        Song lyrics text, or message if lyrics unavailable.
    """
    from .clients.ytmusic import get_ytmusic_client

    ytmusic = get_ytmusic_client()
    result = ytmusic.get_lyrics(browse_id)
    if result and result.get("lyrics"):
        return result["lyrics"]
    return "Lyrics not available for this song."


@mcp.tool()
async def ytmusic_home() -> str:
    """Get the YouTube Music home page with personalized recommendations.

    Requires OAuth authentication.

    Returns:
        Sections of recommended playlists, albums, and mixes.
    """
    from .clients.ytmusic import get_ytmusic_client

    ytmusic = get_ytmusic_client(require_auth=True)
    return _format_json(ytmusic.get_home())


@mcp.tool()
async def ytmusic_charts(country: str = "US") -> str:
    """Get YouTube Music charts (top songs, trending, top artists).

    Args:
        country: ISO 3166-1 alpha-2 country code (default: US)

    Returns:
        Chart data with top songs, trending videos, and top artists.
    """
    from .clients.ytmusic import get_ytmusic_client

    ytmusic = get_ytmusic_client()
    return _format_json(ytmusic.get_charts(country))


@mcp.tool()
async def ytmusic_new_releases() -> str:
    """Get new music releases on YouTube Music.

    Returns:
        New albums and singles.
    """
    from .clients.ytmusic import get_ytmusic_client

    ytmusic = get_ytmusic_client()
    return _format_json(ytmusic.get_new_releases())


# ─── Group 9: YouTube Music Library (OAuth required) ────────────────────────


@mcp.tool()
async def ytmusic_library_playlists(limit: int = 25) -> str:
    """List your YouTube Music playlists.

    Args:
        limit: Max playlists to return (default 25)

    Returns:
        JSON array of playlists with titles, track counts, and IDs.
    """
    from .clients.ytmusic import get_ytmusic_client

    ytmusic = get_ytmusic_client(require_auth=True)
    return _format_json(ytmusic.get_library_playlists(limit))


@mcp.tool()
async def ytmusic_liked_songs(limit: int = 100) -> str:
    """Get your liked songs on YouTube Music.

    Args:
        limit: Max songs to return (default 100)

    Returns:
        JSON array of liked songs with artists, albums, and durations.
    """
    from .clients.ytmusic import get_ytmusic_client

    ytmusic = get_ytmusic_client(require_auth=True)
    return _format_json(ytmusic.get_liked_songs(limit))


@mcp.tool()
async def ytmusic_history() -> str:
    """Get your YouTube Music listening history.

    Returns:
        Recently played songs in reverse chronological order.
    """
    from .clients.ytmusic import get_ytmusic_client

    ytmusic = get_ytmusic_client(require_auth=True)
    return _format_json(ytmusic.get_history())


@mcp.tool()
async def ytmusic_rate_song(
    video_id: str,
    rating: str = "LIKE",
) -> str:
    """Like, dislike, or remove rating on a song.

    Args:
        video_id: YouTube Music song/video ID
        rating: LIKE, DISLIKE, or INDIFFERENT (removes rating)

    Returns:
        Confirmation of the rating action.
    """
    from .clients.ytmusic import get_ytmusic_client

    ytmusic = get_ytmusic_client(require_auth=True)
    ytmusic.rate_song(video_id, rating)
    return f"Rated song {video_id} as {rating}."


# ─── Group 10: YouTube Music Playlist CRUD (OAuth required) ─────────────────


@mcp.tool()
async def ytmusic_playlist_create(
    title: str,
    description: str = "",
    privacy_status: str = "PRIVATE",
    video_ids: list[str] | None = None,
) -> str:
    """Create a new YouTube Music playlist.

    Args:
        title: Playlist title
        description: Playlist description
        privacy_status: PRIVATE, PUBLIC, or UNLISTED
        video_ids: Optional list of song/video IDs to add initially

    Returns:
        The new playlist ID.
    """
    from .clients.ytmusic import get_ytmusic_client

    ytmusic = get_ytmusic_client(require_auth=True)
    playlist_id = ytmusic.create_playlist(
        title, description, privacy_status, video_ids=video_ids
    )
    return f"Created playlist '{title}' with ID: {playlist_id}"


@mcp.tool()
async def ytmusic_playlist_add_items(
    playlist_id: str,
    video_ids: list[str],
) -> str:
    """Add songs to a YouTube Music playlist.

    Args:
        playlist_id: Target playlist ID
        video_ids: List of song/video IDs to add

    Returns:
        Confirmation with number of items added.
    """
    from .clients.ytmusic import get_ytmusic_client

    ytmusic = get_ytmusic_client(require_auth=True)
    result = ytmusic.add_playlist_items(playlist_id, video_ids)
    return f"Added {len(video_ids)} items to playlist {playlist_id}. Status: {result.get('status', 'ok')}"


@mcp.tool()
async def ytmusic_playlist_delete(playlist_id: str) -> str:
    """Delete a YouTube Music playlist.

    Args:
        playlist_id: Playlist ID to delete

    Returns:
        Confirmation of deletion.
    """
    from .clients.ytmusic import get_ytmusic_client

    ytmusic = get_ytmusic_client(require_auth=True)
    ytmusic.delete_playlist(playlist_id)
    return f"Deleted playlist {playlist_id}."


# ─── Formatting Helpers ─────────────────────────────────────────────────────


def _format_json(data: dict | list) -> str:
    """Format data as compact JSON for token efficiency."""
    import json

    return json.dumps(data, indent=2, default=str)


def _format_search_results(response: dict) -> str:
    """Format YouTube search results into a concise summary."""
    import json

    items = response.get("items", [])
    results = []
    for item in items:
        snippet = item.get("snippet", {})
        result = {
            "type": item.get("id", {}).get("kind", "").split("#")[-1],
            "id": (
                item.get("id", {}).get("videoId")
                or item.get("id", {}).get("channelId")
                or item.get("id", {}).get("playlistId")
            ),
            "title": snippet.get("title"),
            "channel": snippet.get("channelTitle"),
            "published": snippet.get("publishedAt"),
            "description": snippet.get("description", "")[:200],
        }
        results.append(result)
    return json.dumps(results, indent=2)


def _format_video_results(response: dict) -> str:
    """Format YouTube video details into a concise summary."""
    import json

    items = response.get("items", [])
    results = []
    for item in items:
        snippet = item.get("snippet", {})
        stats = item.get("statistics", {})
        content = item.get("contentDetails", {})
        result = {
            "id": item.get("id"),
            "title": snippet.get("title"),
            "channel": snippet.get("channelTitle"),
            "published": snippet.get("publishedAt"),
            "duration": content.get("duration"),
            "views": stats.get("viewCount"),
            "likes": stats.get("likeCount"),
            "comments": stats.get("commentCount"),
            "description": snippet.get("description", "")[:300],
            "tags": snippet.get("tags", [])[:10],
        }
        results.append(result)
    return json.dumps(results, indent=2)


def _format_channel_results(response: dict) -> str:
    """Format YouTube channel details."""
    import json

    items = response.get("items", [])
    results = []
    for item in items:
        snippet = item.get("snippet", {})
        stats = item.get("statistics", {})
        result = {
            "id": item.get("id"),
            "title": snippet.get("title"),
            "description": snippet.get("description", "")[:300],
            "subscribers": stats.get("subscriberCount"),
            "videos": stats.get("videoCount"),
            "views": stats.get("viewCount"),
            "custom_url": snippet.get("customUrl"),
            "country": snippet.get("country"),
        }
        results.append(result)
    return json.dumps(results, indent=2)


def _format_ytmusic_results(results: list) -> str:
    """Format YouTube Music search results."""
    import json

    return json.dumps(results[:20], indent=2, default=str)
