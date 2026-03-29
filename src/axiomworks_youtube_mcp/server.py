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


# ─── Group 2b: Subscriptions (OAuth required) ─────────────────────────────────


@mcp.tool()
async def youtube_subscriptions_list(
    max_results: int = 25,
    order: str = "relevance",
    page_token: str | None = None,
) -> str:
    """List the authenticated user's subscriptions.

    Args:
        max_results: Number of subscriptions to return (1-50, default 25)
        order: Sort order — relevance, unread, alphabetical
        page_token: Token for pagination

    Returns:
        JSON array of subscribed channels with IDs, titles, and thumbnails.
    """
    from .clients.youtube import get_youtube_client

    creds = require_oauth()
    youtube = get_youtube_client(credentials=creds)

    params: dict = {
        "part": "snippet,contentDetails",
        "mine": True,
        "maxResults": min(max_results, 50),
        "order": order,
    }
    if page_token:
        params["pageToken"] = page_token

    response = youtube.subscriptions().list(**params).execute()
    return _format_json(response)


@mcp.tool()
async def youtube_subscribe(channel_id: str) -> str:
    """Subscribe to a YouTube channel.

    Args:
        channel_id: The channel ID to subscribe to

    Returns:
        Confirmation of the subscription.
    """
    from .clients.youtube import get_youtube_client

    creds = require_oauth()
    youtube = get_youtube_client(credentials=creds)

    body = {
        "snippet": {
            "resourceId": {
                "kind": "youtube#channel",
                "channelId": channel_id,
            }
        }
    }
    response = youtube.subscriptions().insert(part="snippet", body=body).execute()
    title = response.get("snippet", {}).get("title", channel_id)
    return f"Subscribed to channel: {title} ({channel_id})"


@mcp.tool()
async def youtube_unsubscribe(subscription_id: str) -> str:
    """Unsubscribe from a YouTube channel.

    The subscription_id comes from youtube_subscriptions_list.

    Args:
        subscription_id: The subscription resource ID to remove

    Returns:
        Confirmation of the unsubscription.
    """
    from .clients.youtube import get_youtube_client

    creds = require_oauth()
    youtube = get_youtube_client(credentials=creds)

    youtube.subscriptions().delete(id=subscription_id).execute()
    return f"Unsubscribed (subscription ID: {subscription_id})"


# ─── Group 4: Playlist Operations ─────────────────────────────────────────────


@mcp.tool()
async def youtube_playlist_details(
    playlist_id: str,
    max_results: int = 25,
    page_token: str | None = None,
) -> str:
    """Get playlist metadata and its video items.

    Args:
        playlist_id: YouTube playlist ID
        max_results: Number of items to return (1-50, default 25)
        page_token: Token for pagination through playlist items

    Returns:
        Playlist metadata and JSON array of video items with titles and positions.
    """
    from .clients.youtube import get_youtube_client

    api_key = require_api_key()
    youtube = get_youtube_client(api_key=api_key)

    # Get playlist metadata
    pl_response = youtube.playlists().list(
        part="snippet,contentDetails,status",
        id=playlist_id,
    ).execute()

    # Get playlist items
    params: dict = {
        "part": "snippet,contentDetails,status",
        "playlistId": playlist_id,
        "maxResults": min(max_results, 50),
    }
    if page_token:
        params["pageToken"] = page_token

    items_response = youtube.playlistItems().list(**params).execute()

    result = {
        "playlist": pl_response.get("items", [{}])[0] if pl_response.get("items") else {},
        "items": items_response.get("items", []),
        "totalResults": items_response.get("pageInfo", {}).get("totalResults"),
        "nextPageToken": items_response.get("nextPageToken"),
    }
    return _format_json(result)


@mcp.tool()
async def youtube_playlist_create(
    title: str,
    description: str = "",
    privacy_status: str = "private",
    tags: list[str] | None = None,
) -> str:
    """Create a new YouTube playlist.

    Args:
        title: Playlist title
        description: Playlist description
        privacy_status: private, public, or unlisted (default: private)
        tags: Optional list of tags

    Returns:
        The new playlist ID and confirmation.
    """
    from .clients.youtube import get_youtube_client

    creds = require_oauth()
    youtube = get_youtube_client(credentials=creds)

    body: dict = {
        "snippet": {
            "title": title,
            "description": description,
        },
        "status": {
            "privacyStatus": privacy_status,
        },
    }
    if tags:
        body["snippet"]["tags"] = tags

    response = youtube.playlists().insert(part="snippet,status", body=body).execute()
    playlist_id = response.get("id")
    return f"Created playlist '{title}' with ID: {playlist_id}"


@mcp.tool()
async def youtube_playlist_delete(playlist_id: str) -> str:
    """Delete a YouTube playlist.

    Args:
        playlist_id: The playlist ID to delete

    Returns:
        Confirmation of deletion.
    """
    from .clients.youtube import get_youtube_client

    creds = require_oauth()
    youtube = get_youtube_client(credentials=creds)

    youtube.playlists().delete(id=playlist_id).execute()
    return f"Deleted playlist {playlist_id}."


@mcp.tool()
async def youtube_playlist_add_video(
    playlist_id: str,
    video_id: str,
    position: int | None = None,
) -> str:
    """Add a video to a YouTube playlist.

    Args:
        playlist_id: Target playlist ID
        video_id: Video ID to add
        position: Optional position in the playlist (0-based)

    Returns:
        Confirmation with the playlist item ID.
    """
    from .clients.youtube import get_youtube_client

    creds = require_oauth()
    youtube = get_youtube_client(credentials=creds)

    body: dict = {
        "snippet": {
            "playlistId": playlist_id,
            "resourceId": {
                "kind": "youtube#video",
                "videoId": video_id,
            },
        }
    }
    if position is not None:
        body["snippet"]["position"] = position

    response = youtube.playlistItems().insert(part="snippet", body=body).execute()
    item_id = response.get("id")
    return f"Added video {video_id} to playlist {playlist_id} (item ID: {item_id})"


@mcp.tool()
async def youtube_playlist_remove_video(playlist_item_id: str) -> str:
    """Remove a video from a YouTube playlist.

    The playlist_item_id comes from youtube_playlist_details (the item's 'id' field),
    NOT the video ID.

    Args:
        playlist_item_id: The playlist item resource ID to remove

    Returns:
        Confirmation of removal.
    """
    from .clients.youtube import get_youtube_client

    creds = require_oauth()
    youtube = get_youtube_client(credentials=creds)

    youtube.playlistItems().delete(id=playlist_item_id).execute()
    return f"Removed playlist item {playlist_item_id}."


@mcp.tool()
async def youtube_my_playlists(
    max_results: int = 25,
    page_token: str | None = None,
) -> str:
    """List the authenticated user's YouTube playlists.

    Args:
        max_results: Number of playlists to return (1-50, default 25)
        page_token: Token for pagination

    Returns:
        JSON array of playlists with titles, descriptions, item counts, and IDs.
    """
    from .clients.youtube import get_youtube_client

    creds = require_oauth()
    youtube = get_youtube_client(credentials=creds)

    params: dict = {
        "part": "snippet,contentDetails,status",
        "mine": True,
        "maxResults": min(max_results, 50),
    }
    if page_token:
        params["pageToken"] = page_token

    response = youtube.playlists().list(**params).execute()
    return _format_json(response)


# ─── Group 5: Comment Operations ──────────────────────────────────────────────


@mcp.tool()
async def youtube_comments_list(
    video_id: str,
    max_results: int = 20,
    order: str = "relevance",
    page_token: str | None = None,
) -> str:
    """Get top-level comments on a video.

    Args:
        video_id: YouTube video ID
        max_results: Number of comment threads to return (1-100, default 20)
        order: Sort order — relevance or time
        page_token: Token for pagination

    Returns:
        JSON array of comment threads with author, text, likes, and reply counts.
    """
    from .clients.youtube import get_youtube_client

    api_key = require_api_key()
    youtube = get_youtube_client(api_key=api_key)

    params: dict = {
        "part": "snippet,replies",
        "videoId": video_id,
        "maxResults": min(max_results, 100),
        "order": order,
        "textFormat": "plainText",
    }
    if page_token:
        params["pageToken"] = page_token

    response = youtube.commentThreads().list(**params).execute()
    return _format_comment_threads(response)


@mcp.tool()
async def youtube_comment_replies(
    parent_id: str,
    max_results: int = 20,
    page_token: str | None = None,
) -> str:
    """Get replies to a specific comment.

    Args:
        parent_id: The top-level comment ID to get replies for
        max_results: Number of replies to return (1-100, default 20)
        page_token: Token for pagination

    Returns:
        JSON array of reply comments with author, text, and likes.
    """
    from .clients.youtube import get_youtube_client

    api_key = require_api_key()
    youtube = get_youtube_client(api_key=api_key)

    params: dict = {
        "part": "snippet",
        "parentId": parent_id,
        "maxResults": min(max_results, 100),
        "textFormat": "plainText",
    }
    if page_token:
        params["pageToken"] = page_token

    response = youtube.comments().list(**params).execute()
    return _format_json(response)


@mcp.tool()
async def youtube_comment_post(
    video_id: str,
    text: str,
) -> str:
    """Post a top-level comment on a video.

    Args:
        video_id: YouTube video ID to comment on
        text: Comment text

    Returns:
        The new comment ID and confirmation.
    """
    from .clients.youtube import get_youtube_client

    creds = require_oauth()
    youtube = get_youtube_client(credentials=creds)

    body = {
        "snippet": {
            "videoId": video_id,
            "topLevelComment": {
                "snippet": {
                    "textOriginal": text,
                }
            },
        }
    }
    response = youtube.commentThreads().insert(part="snippet", body=body).execute()
    comment_id = response.get("id")
    return f"Posted comment on video {video_id} (comment ID: {comment_id})"


@mcp.tool()
async def youtube_comment_reply(
    parent_id: str,
    text: str,
) -> str:
    """Reply to an existing comment.

    Args:
        parent_id: The comment ID to reply to
        text: Reply text

    Returns:
        The new reply comment ID and confirmation.
    """
    from .clients.youtube import get_youtube_client

    creds = require_oauth()
    youtube = get_youtube_client(credentials=creds)

    body = {
        "snippet": {
            "parentId": parent_id,
            "textOriginal": text,
        }
    }
    response = youtube.comments().insert(part="snippet", body=body).execute()
    reply_id = response.get("id")
    return f"Posted reply to comment {parent_id} (reply ID: {reply_id})"


@mcp.tool()
async def youtube_comment_delete(comment_id: str) -> str:
    """Delete a comment or reply.

    You can only delete comments you own.

    Args:
        comment_id: The comment ID to delete

    Returns:
        Confirmation of deletion.
    """
    from .clients.youtube import get_youtube_client

    creds = require_oauth()
    youtube = get_youtube_client(credentials=creds)

    youtube.comments().delete(id=comment_id).execute()
    return f"Deleted comment {comment_id}."


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


# ─── Group 9b: YouTube Music Library — Songs, Albums, Artists (OAuth) ──────


@mcp.tool()
async def ytmusic_library_songs(
    limit: int = 100,
    order: str | None = None,
) -> str:
    """List saved songs in your YouTube Music library.

    Args:
        limit: Max songs to return (default 100)
        order: Optional sort — a_to_z, z_to_a, recently_added

    Returns:
        JSON array of library songs with titles, artists, albums, and durations.
    """
    from .clients.ytmusic import get_ytmusic_client

    ytmusic = get_ytmusic_client(require_auth=True)
    kwargs: dict = {"limit": limit}
    if order:
        kwargs["order"] = order
    return _format_json(ytmusic.get_library_songs(**kwargs))


@mcp.tool()
async def ytmusic_library_albums(
    limit: int = 100,
    order: str | None = None,
) -> str:
    """List saved albums in your YouTube Music library.

    Args:
        limit: Max albums to return (default 100)
        order: Optional sort — a_to_z, z_to_a, recently_added

    Returns:
        JSON array of library albums with titles, artists, and browse IDs.
    """
    from .clients.ytmusic import get_ytmusic_client

    ytmusic = get_ytmusic_client(require_auth=True)
    kwargs: dict = {"limit": limit}
    if order:
        kwargs["order"] = order
    return _format_json(ytmusic.get_library_albums(**kwargs))


@mcp.tool()
async def ytmusic_library_artists(
    limit: int = 100,
    order: str | None = None,
) -> str:
    """List followed/subscribed artists in your YouTube Music library.

    Args:
        limit: Max artists to return (default 100)
        order: Optional sort — a_to_z, z_to_a, recently_added

    Returns:
        JSON array of library artists with names and channel IDs.
    """
    from .clients.ytmusic import get_ytmusic_client

    ytmusic = get_ytmusic_client(require_auth=True)
    kwargs: dict = {"limit": limit}
    if order:
        kwargs["order"] = order
    return _format_json(ytmusic.get_library_artists(**kwargs))


@mcp.tool()
async def ytmusic_subscribe_artist(channel_id: str) -> str:
    """Subscribe to an artist on YouTube Music.

    Args:
        channel_id: The artist's channel ID

    Returns:
        Confirmation of subscription.
    """
    from .clients.ytmusic import get_ytmusic_client

    ytmusic = get_ytmusic_client(require_auth=True)
    ytmusic.subscribe_artists([channel_id])
    return f"Subscribed to artist {channel_id}."


@mcp.tool()
async def ytmusic_unsubscribe_artist(channel_id: str) -> str:
    """Unsubscribe from an artist on YouTube Music.

    Args:
        channel_id: The artist's channel ID

    Returns:
        Confirmation of unsubscription.
    """
    from .clients.ytmusic import get_ytmusic_client

    ytmusic = get_ytmusic_client(require_auth=True)
    ytmusic.unsubscribe_artists([channel_id])
    return f"Unsubscribed from artist {channel_id}."


# ─── Group 10b: YouTube Music Playlist Details & Edit (OAuth) ─────────────────


@mcp.tool()
async def ytmusic_playlist_details(
    playlist_id: str,
    limit: int | None = None,
) -> str:
    """Get a YouTube Music playlist's tracks and metadata.

    Works without auth for public playlists. Requires auth for private ones.

    Args:
        playlist_id: YouTube Music playlist ID
        limit: Max tracks to return (default: all)

    Returns:
        Playlist metadata with track listing.
    """
    from .clients.ytmusic import get_ytmusic_client

    # Try authed client first, fall back to public
    try:
        ytmusic = get_ytmusic_client(require_auth=True)
    except ValueError:
        ytmusic = get_ytmusic_client(require_auth=False)

    kwargs: dict = {}
    if limit is not None:
        kwargs["limit"] = limit
    return _format_json(ytmusic.get_playlist(playlist_id, **kwargs))


@mcp.tool()
async def ytmusic_playlist_edit(
    playlist_id: str,
    title: str | None = None,
    description: str | None = None,
    privacy_status: str | None = None,
) -> str:
    """Edit a YouTube Music playlist's metadata.

    Args:
        playlist_id: Playlist ID to edit
        title: New title (optional)
        description: New description (optional)
        privacy_status: New privacy — PRIVATE, PUBLIC, or UNLISTED (optional)

    Returns:
        Confirmation of the edit.
    """
    from .clients.ytmusic import get_ytmusic_client

    ytmusic = get_ytmusic_client(require_auth=True)
    kwargs: dict = {"playlistId": playlist_id}
    if title is not None:
        kwargs["title"] = title
    if description is not None:
        kwargs["description"] = description
    if privacy_status is not None:
        kwargs["privacyStatus"] = privacy_status

    ytmusic.edit_playlist(**kwargs)
    return f"Updated playlist {playlist_id}."


@mcp.tool()
async def ytmusic_playlist_remove_items(
    playlist_id: str,
    video_ids: list[str],
) -> str:
    """Remove songs from a YouTube Music playlist.

    The video_ids should be the setVideoId values from ytmusic_playlist_details,
    NOT regular video IDs.

    Args:
        playlist_id: Playlist ID to remove from
        video_ids: List of setVideoId values to remove

    Returns:
        Confirmation with number of items removed.
    """
    from .clients.ytmusic import get_ytmusic_client

    ytmusic = get_ytmusic_client(require_auth=True)
    # ytmusicapi expects list of dicts with videoId and setVideoId
    videos = [{"videoId": vid, "setVideoId": vid} for vid in video_ids]
    ytmusic.remove_playlist_items(playlist_id, videos)
    return f"Removed {len(video_ids)} items from playlist {playlist_id}."


# ─── Group 8b: YouTube Music Browse — Moods, Radio, Podcasts ──────────────────


@mcp.tool()
async def ytmusic_moods() -> str:
    """Browse available mood and genre categories on YouTube Music.

    Returns:
        JSON object of mood/genre categories with their params for fetching playlists.
    """
    from .clients.ytmusic import get_ytmusic_client

    ytmusic = get_ytmusic_client()
    return _format_json(ytmusic.get_mood_categories())


@mcp.tool()
async def ytmusic_mood_playlists(params: str) -> str:
    """Get playlists for a specific mood or genre category.

    The params value comes from ytmusic_moods response.

    Args:
        params: The category params string from ytmusic_moods

    Returns:
        JSON array of playlists for the selected mood/genre.
    """
    from .clients.ytmusic import get_ytmusic_client

    ytmusic = get_ytmusic_client()
    return _format_json(ytmusic.get_mood_playlists(params))


@mcp.tool()
async def ytmusic_get_watch_playlist(
    video_id: str | None = None,
    playlist_id: str | None = None,
    limit: int = 25,
) -> str:
    """Get the radio/up-next queue for a song or playlist.

    Provide either video_id or playlist_id. Returns the auto-generated
    queue with lyrics browse IDs and related tracks.

    Args:
        video_id: Song video ID to get radio for
        playlist_id: Playlist ID to get queue for
        limit: Max tracks in queue (default 25)

    Returns:
        Watch playlist with tracks, lyrics IDs, and related content.
    """
    from .clients.ytmusic import get_ytmusic_client

    ytmusic = get_ytmusic_client()
    kwargs: dict = {"limit": limit}
    if video_id:
        kwargs["videoId"] = video_id
    if playlist_id:
        kwargs["playlistId"] = playlist_id

    if not video_id and not playlist_id:
        raise ValueError("Provide either video_id or playlist_id")

    return _format_json(ytmusic.get_watch_playlist(**kwargs))


@mcp.tool()
async def ytmusic_get_podcast(podcast_id: str) -> str:
    """Get podcast details and episode listing.

    Args:
        podcast_id: YouTube Music podcast browse ID

    Returns:
        Podcast metadata with episode list.
    """
    from .clients.ytmusic import get_ytmusic_client

    ytmusic = get_ytmusic_client()
    return _format_json(ytmusic.get_podcast(podcast_id))


@mcp.tool()
async def ytmusic_get_episode(episode_id: str) -> str:
    """Get details for a specific podcast episode.

    Args:
        episode_id: YouTube Music episode video ID

    Returns:
        Episode metadata with title, description, duration, and podcast info.
    """
    from .clients.ytmusic import get_ytmusic_client

    ytmusic = get_ytmusic_client()
    return _format_json(ytmusic.get_episode(episode_id))


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


def _format_comment_threads(response: dict) -> str:
    """Format YouTube comment threads into a concise summary."""
    import json

    items = response.get("items", [])
    results = []
    for item in items:
        top_comment = item.get("snippet", {}).get("topLevelComment", {})
        snippet = top_comment.get("snippet", {})
        result = {
            "id": top_comment.get("id"),
            "author": snippet.get("authorDisplayName"),
            "text": snippet.get("textDisplay"),
            "likes": snippet.get("likeCount"),
            "published": snippet.get("publishedAt"),
            "updated": snippet.get("updatedAt"),
            "reply_count": item.get("snippet", {}).get("totalReplyCount", 0),
        }
        # Include first few replies if present
        replies = item.get("replies", {}).get("comments", [])
        if replies:
            result["replies"] = [
                {
                    "id": r.get("id"),
                    "author": r.get("snippet", {}).get("authorDisplayName"),
                    "text": r.get("snippet", {}).get("textDisplay"),
                    "likes": r.get("snippet", {}).get("likeCount"),
                    "published": r.get("snippet", {}).get("publishedAt"),
                }
                for r in replies[:5]
            ]
        results.append(result)

    output = {
        "comments": results,
        "nextPageToken": response.get("nextPageToken"),
        "totalResults": response.get("pageInfo", {}).get("totalResults"),
    }
    return json.dumps(output, indent=2)


def _format_ytmusic_results(results: list) -> str:
    """Format YouTube Music search results."""
    import json

    return json.dumps(results[:20], indent=2, default=str)

def _format_analytics_response(response: dict) -> str:
    """Format YouTube Analytics API response."""
    import json

    result = {
        "columnHeaders": response.get("columnHeaders", []),
        "rows": response.get("rows", []),
    }
    return json.dumps(result, indent=2, default=str)


# ─── Group 1 Addition: Video Categories (API key) ───────────────────────────


@mcp.tool()
async def youtube_categories(
    region_code: str = "US",
) -> str:
    """List video categories available for a region.

    Args:
        region_code: ISO 3166-1 alpha-2 country code (default: US)

    Returns:
        JSON array of video categories with IDs and titles.
    """
    from .clients.youtube import get_youtube_client

    api_key = require_api_key()
    youtube = get_youtube_client(api_key=api_key)

    response = (
        youtube.videoCategories()
        .list(part="snippet", regionCode=region_code)
        .execute()
    )
    return _format_json(response)


# ─── Group 2 Additions: Video Operations (OAuth) ────────────────────────────


@mcp.tool()
async def youtube_video_rate(
    video_id: str,
    rating: str = "like",
) -> str:
    """Like, dislike, or remove rating on a YouTube video.

    Args:
        video_id: YouTube video ID
        rating: Rating action — like, dislike, or none (removes rating)

    Returns:
        Confirmation of the rating action.
    """
    from .clients.youtube import get_youtube_client

    creds = require_oauth()
    youtube = get_youtube_client(credentials=creds)

    youtube.videos().rate(id=video_id, rating=rating).execute()
    return f"Rated video {video_id} as '{rating}'."


@mcp.tool()
async def youtube_video_get_rating(
    video_ids: str,
) -> str:
    """Get the authenticated user's rating on one or more videos.

    Args:
        video_ids: Comma-separated video IDs

    Returns:
        JSON with rating info for each video (like/dislike/none/unspecified).
    """
    from .clients.youtube import get_youtube_client

    creds = require_oauth()
    youtube = get_youtube_client(credentials=creds)

    response = youtube.videos().getRating(id=video_ids).execute()
    return _format_json(response)


@mcp.tool()
async def youtube_video_upload(
    file_path: str,
    title: str,
    description: str = "",
    tags: list[str] | None = None,
    category_id: str = "22",
    privacy_status: str = "private",
) -> str:
    """Upload a video to YouTube.

    Args:
        file_path: Local path to the video file
        title: Video title
        description: Video description
        tags: Optional list of tags
        category_id: Video category ID (default: 22 = People & Blogs)
        privacy_status: private, public, or unlisted (default: private)

    Returns:
        The new video ID and confirmation.
    """
    from googleapiclient.http import MediaFileUpload
    from .clients.youtube import get_youtube_client

    creds = require_oauth()
    youtube = get_youtube_client(credentials=creds)

    body: dict = {
        "snippet": {
            "title": title,
            "description": description,
            "categoryId": category_id,
        },
        "status": {
            "privacyStatus": privacy_status,
        },
    }
    if tags:
        body["snippet"]["tags"] = tags

    media = MediaFileUpload(file_path, resumable=True)
    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media,
    )

    response = None
    while response is None:
        _, response = request.next_chunk()

    video_id = response.get("id")
    return f"Uploaded video '{title}' with ID: {video_id}"


@mcp.tool()
async def youtube_video_update(
    video_id: str,
    title: str | None = None,
    description: str | None = None,
    tags: list[str] | None = None,
    category_id: str | None = None,
    privacy_status: str | None = None,
) -> str:
    """Update metadata for an existing YouTube video.

    Args:
        video_id: YouTube video ID to update
        title: New title (optional)
        description: New description (optional)
        tags: New tags list (optional)
        category_id: New category ID (optional)
        privacy_status: New privacy — private, public, or unlisted (optional)

    Returns:
        Confirmation of the update.
    """
    from .clients.youtube import get_youtube_client

    creds = require_oauth()
    youtube = get_youtube_client(credentials=creds)

    # Fetch current video data to merge with updates
    current = (
        youtube.videos()
        .list(part="snippet,status", id=video_id)
        .execute()
    )
    if not current.get("items"):
        raise ValueError(f"Video {video_id} not found.")

    item = current["items"][0]
    snippet = item.get("snippet", {})
    status = item.get("status", {})

    body: dict = {
        "id": video_id,
        "snippet": {
            "title": title if title is not None else snippet.get("title"),
            "description": description if description is not None else snippet.get("description", ""),
            "categoryId": category_id if category_id is not None else snippet.get("categoryId"),
            "tags": tags if tags is not None else snippet.get("tags", []),
        },
        "status": {
            "privacyStatus": privacy_status if privacy_status is not None else status.get("privacyStatus"),
        },
    }

    youtube.videos().update(part="snippet,status", body=body).execute()
    return f"Updated video {video_id}."


@mcp.tool()
async def youtube_video_delete(video_id: str) -> str:
    """Delete a YouTube video.

    You can only delete videos you own.

    Args:
        video_id: YouTube video ID to delete

    Returns:
        Confirmation of deletion.
    """
    from .clients.youtube import get_youtube_client

    creds = require_oauth()
    youtube = get_youtube_client(credentials=creds)

    youtube.videos().delete(id=video_id).execute()
    return f"Deleted video {video_id}."


@mcp.tool()
async def youtube_thumbnail_set(
    video_id: str,
    file_path: str,
) -> str:
    """Upload a custom thumbnail for a video.

    Args:
        video_id: YouTube video ID
        file_path: Local path to the thumbnail image (JPEG, PNG, GIF, BMP)

    Returns:
        Confirmation with thumbnail URL.
    """
    from googleapiclient.http import MediaFileUpload
    from .clients.youtube import get_youtube_client

    creds = require_oauth()
    youtube = get_youtube_client(credentials=creds)

    media = MediaFileUpload(file_path, mimetype="image/jpeg")
    response = youtube.thumbnails().set(
        videoId=video_id,
        media_body=media,
    ).execute()

    url = response.get("items", [{}])[0].get("default", {}).get("url", "")
    return f"Set thumbnail for video {video_id}. URL: {url}"


# ─── Group 3 Additions: Channel Operations (API key) ────────────────────────


@mcp.tool()
async def youtube_channel_videos(
    channel_id: str,
    max_results: int = 10,
    order: str = "date",
    published_after: str | None = None,
) -> str:
    """List videos from a specific channel.

    Args:
        channel_id: YouTube channel ID
        max_results: Number of results (1-50, default 10)
        order: Sort order — date, rating, viewCount, relevance, title
        published_after: ISO 8601 date filter (e.g., 2026-01-01T00:00:00Z)

    Returns:
        JSON array of videos from the channel.
    """
    from .clients.youtube import get_youtube_client

    api_key = require_api_key()
    youtube = get_youtube_client(api_key=api_key)

    params: dict = {
        "part": "snippet",
        "channelId": channel_id,
        "type": "video",
        "maxResults": min(max_results, 50),
        "order": order,
    }
    if published_after:
        params["publishedAfter"] = published_after

    response = youtube.search().list(**params).execute()
    return _format_search_results(response)


@mcp.tool()
async def youtube_channel_sections(
    channel_id: str,
) -> str:
    """Get the sections displayed on a channel's page.

    Args:
        channel_id: YouTube channel ID

    Returns:
        JSON array of channel sections with types and content.
    """
    from .clients.youtube import get_youtube_client

    api_key = require_api_key()
    youtube = get_youtube_client(api_key=api_key)

    response = (
        youtube.channelSections()
        .list(part="snippet,contentDetails", channelId=channel_id)
        .execute()
    )
    return _format_json(response)


# ─── Group 4 Addition: Playlist Update (OAuth) ──────────────────────────────


@mcp.tool()
async def youtube_playlist_update(
    playlist_id: str,
    title: str | None = None,
    description: str | None = None,
    privacy_status: str | None = None,
) -> str:
    """Update metadata for an existing YouTube playlist.

    Args:
        playlist_id: Playlist ID to update
        title: New title (optional)
        description: New description (optional)
        privacy_status: New privacy — private, public, or unlisted (optional)

    Returns:
        Confirmation of the update.
    """
    from .clients.youtube import get_youtube_client

    creds = require_oauth()
    youtube = get_youtube_client(credentials=creds)

    # Fetch current playlist data to merge with updates
    current = (
        youtube.playlists()
        .list(part="snippet,status", id=playlist_id)
        .execute()
    )
    if not current.get("items"):
        raise ValueError(f"Playlist {playlist_id} not found.")

    item = current["items"][0]
    snippet = item.get("snippet", {})
    status = item.get("status", {})

    body: dict = {
        "id": playlist_id,
        "snippet": {
            "title": title if title is not None else snippet.get("title"),
            "description": description if description is not None else snippet.get("description", ""),
        },
        "status": {
            "privacyStatus": privacy_status if privacy_status is not None else status.get("privacyStatus"),
        },
    }

    youtube.playlists().update(part="snippet,status", body=body).execute()
    return f"Updated playlist {playlist_id}."


# ─── Group 5 Additions: Comment Operations (OAuth) ──────────────────────────


@mcp.tool()
async def youtube_comment_update(
    comment_id: str,
    text: str,
) -> str:
    """Edit an existing comment.

    You can only edit comments you own.

    Args:
        comment_id: The comment ID to edit
        text: New comment text

    Returns:
        Confirmation of the update.
    """
    from .clients.youtube import get_youtube_client

    creds = require_oauth()
    youtube = get_youtube_client(credentials=creds)

    body = {
        "id": comment_id,
        "snippet": {
            "textOriginal": text,
        },
    }
    youtube.comments().update(part="snippet", body=body).execute()
    return f"Updated comment {comment_id}."


@mcp.tool()
async def youtube_comment_moderate(
    comment_ids: str,
    moderation_status: str,
    ban_author: bool = False,
) -> str:
    """Set the moderation status of one or more comments.

    Args:
        comment_ids: Comma-separated comment IDs
        moderation_status: heldForReview, published, or rejected
        ban_author: If True, also bans the comment author (default: False)

    Returns:
        Confirmation of the moderation action.
    """
    from .clients.youtube import get_youtube_client

    creds = require_oauth()
    youtube = get_youtube_client(credentials=creds)

    youtube.comments().setModerationStatus(
        id=comment_ids,
        moderationStatus=moderation_status,
        banAuthor=ban_author,
    ).execute()
    return f"Set moderation status to '{moderation_status}' for comment(s): {comment_ids}"


# ─── Group 6: YouTube Analytics (OAuth required) ────────────────────────────


@mcp.tool()
async def youtube_analytics_query(
    start_date: str,
    end_date: str,
    metrics: str,
    dimensions: str | None = None,
    filters: str | None = None,
    sort: str | None = None,
    max_results: int = 200,
) -> str:
    """Run a flexible YouTube Analytics query.

    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        metrics: Comma-separated metrics (e.g., views,estimatedMinutesWatched,likes)
        dimensions: Comma-separated dimensions (e.g., day, video, country)
        filters: Filter expression (e.g., video==VIDEO_ID;country==US)
        sort: Sort order (e.g., -views for descending)
        max_results: Max rows to return (default 200)

    Returns:
        Analytics data with column headers and rows.
    """
    from .clients.analytics import get_analytics_client

    creds = require_oauth()
    analytics = get_analytics_client(credentials=creds)

    params: dict = {
        "ids": "channel==MINE",
        "startDate": start_date,
        "endDate": end_date,
        "metrics": metrics,
        "maxResults": max_results,
    }
    if dimensions:
        params["dimensions"] = dimensions
    if filters:
        params["filters"] = filters
    if sort:
        params["sort"] = sort

    response = analytics.reports().query(**params).execute()
    return _format_analytics_response(response)


@mcp.tool()
async def youtube_analytics_video(
    video_id: str,
    start_date: str,
    end_date: str,
    metrics: str = "views,estimatedMinutesWatched,likes,comments",
) -> str:
    """Get analytics for a specific video.

    Args:
        video_id: YouTube video ID
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        metrics: Comma-separated metrics (default: views,estimatedMinutesWatched,likes,comments)

    Returns:
        Video analytics data with the requested metrics.
    """
    from .clients.analytics import get_analytics_client

    creds = require_oauth()
    analytics = get_analytics_client(credentials=creds)

    response = analytics.reports().query(
        ids="channel==MINE",
        startDate=start_date,
        endDate=end_date,
        metrics=metrics,
        filters=f"video=={video_id}",
    ).execute()
    return _format_analytics_response(response)


@mcp.tool()
async def youtube_analytics_top_videos(
    metric: str = "views",
    start_date: str = "",
    end_date: str = "",
    max_results: int = 10,
) -> str:
    """Get top videos ranked by a specific metric.

    Args:
        metric: Metric to rank by — views, estimatedMinutesWatched, or likes
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        max_results: Number of top videos to return (default 10)

    Returns:
        Top videos ranked by the specified metric.
    """
    from .clients.analytics import get_analytics_client

    creds = require_oauth()
    analytics = get_analytics_client(credentials=creds)

    response = analytics.reports().query(
        ids="channel==MINE",
        startDate=start_date,
        endDate=end_date,
        metrics=metric,
        dimensions="video",
        sort=f"-{metric}",
        maxResults=max_results,
    ).execute()
    return _format_analytics_response(response)


@mcp.tool()
async def youtube_analytics_demographics(
    start_date: str,
    end_date: str,
    dimension: str = "ageGroup",
) -> str:
    """Get audience demographics data.

    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        dimension: Demographic dimension — ageGroup, gender, or country

    Returns:
        Viewer demographics breakdown by the specified dimension.
    """
    from .clients.analytics import get_analytics_client

    creds = require_oauth()
    analytics = get_analytics_client(credentials=creds)

    response = analytics.reports().query(
        ids="channel==MINE",
        startDate=start_date,
        endDate=end_date,
        metrics="viewerPercentage",
        dimensions=dimension,
        sort=f"-viewerPercentage",
    ).execute()
    return _format_analytics_response(response)


@mcp.tool()
async def youtube_analytics_revenue(
    start_date: str,
    end_date: str,
    dimensions: str | None = None,
) -> str:
    """Get revenue metrics for the channel.

    Requires the yt-analytics-monetary.readonly scope.

    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        dimensions: Optional dimensions (e.g., day, video, country)

    Returns:
        Revenue data including estimated revenue and ad metrics.
    """
    from .clients.analytics import get_analytics_client

    creds = require_oauth()
    analytics = get_analytics_client(credentials=creds)

    params: dict = {
        "ids": "channel==MINE",
        "startDate": start_date,
        "endDate": end_date,
        "metrics": "estimatedRevenue,estimatedAdRevenue,grossRevenue,estimatedRedPartnerRevenue",
    }
    if dimensions:
        params["dimensions"] = dimensions
        params["sort"] = f"-estimatedRevenue"

    response = analytics.reports().query(**params).execute()
    return _format_analytics_response(response)


# ─── Group 7: Live Streaming (OAuth required) ───────────────────────────────


@mcp.tool()
async def youtube_live_broadcasts(
    broadcast_status: str = "all",
    max_results: int = 10,
) -> str:
    """List live broadcasts for the authenticated user.

    Args:
        broadcast_status: Filter — upcoming, active, completed, or all (default: all)
        max_results: Number of broadcasts to return (1-50, default 10)

    Returns:
        JSON array of live broadcasts with status, scheduled times, and details.
    """
    from .clients.live import get_live_client

    creds = require_oauth()
    youtube = get_live_client(credentials=creds)

    response = (
        youtube.liveBroadcasts()
        .list(
            part="snippet,contentDetails,status",
            broadcastStatus=broadcast_status,
            maxResults=min(max_results, 50),
        )
        .execute()
    )
    return _format_json(response)


@mcp.tool()
async def youtube_live_chat_messages(
    live_chat_id: str,
    max_results: int = 200,
) -> str:
    """Read messages from a live chat.

    The live_chat_id comes from a broadcast's snippet.liveChatId field.

    Args:
        live_chat_id: The live chat ID from the broadcast
        max_results: Number of messages to return (default 200)

    Returns:
        JSON array of chat messages with authors, text, and timestamps.
    """
    from .clients.live import get_live_client

    creds = require_oauth()
    youtube = get_live_client(credentials=creds)

    response = (
        youtube.liveChatMessages()
        .list(
            liveChatId=live_chat_id,
            part="snippet,authorDetails",
            maxResults=min(max_results, 2000),
        )
        .execute()
    )
    return _format_json(response)


@mcp.tool()
async def youtube_live_chat_send(
    live_chat_id: str,
    message_text: str,
) -> str:
    """Send a message to a live chat.

    Args:
        live_chat_id: The live chat ID from the broadcast
        message_text: Text content of the message

    Returns:
        Confirmation with the message ID.
    """
    from .clients.live import get_live_client

    creds = require_oauth()
    youtube = get_live_client(credentials=creds)

    body = {
        "snippet": {
            "liveChatId": live_chat_id,
            "type": "textMessageEvent",
            "textMessageDetails": {
                "messageText": message_text,
            },
        }
    }
    response = youtube.liveChatMessages().insert(part="snippet", body=body).execute()
    msg_id = response.get("id")
    return f"Sent message to live chat {live_chat_id} (message ID: {msg_id})"


# ─── Group 11 Addition: YouTube Music Channel/Podcast ────────────────────────


@mcp.tool()
async def ytmusic_get_channel(channel_id: str) -> str:
    """Get a podcast channel page on YouTube Music.

    Args:
        channel_id: YouTube Music channel ID

    Returns:
        Channel page data with shows, episodes, and metadata.
    """
    from .clients.ytmusic import get_ytmusic_client

    ytmusic = get_ytmusic_client()
    return _format_json(ytmusic.get_channel(channel_id))

