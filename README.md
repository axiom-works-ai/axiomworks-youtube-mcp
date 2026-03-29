# Axiom Works YouTube + YouTube Music MCP Server

The definitive MCP server for YouTube and YouTube Music. **68 tools** across search, playlists, comments, analytics, live streaming, and full YouTube Music library management.

No other YouTube MCP server covers analytics, live streaming, comments (write), video uploads, **or** YouTube Music. This one covers all of them.

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

## Quick Start

```bash
# Install
pip install axiomworks-youtube-mcp

# Or run directly with uvx (zero install)
uvx axiomworks-youtube-mcp run
```

### Add to Claude Code

```json
{
  "mcpServers": {
    "youtube": {
      "command": "uvx",
      "args": ["axiomworks-youtube-mcp", "run"]
    }
  }
}
```

### Add to Claude Desktop

```json
{
  "mcpServers": {
    "youtube": {
      "command": "uvx",
      "args": ["axiomworks-youtube-mcp", "run"]
    }
  }
}
```

## Setup

The server works immediately with zero configuration (Tier 0). Add credentials to unlock more features:

```bash
axiomworks-youtube-mcp setup
```

| Tier | Setup Time | What You Get |
|------|-----------|-------------|
| **Tier 0** — Zero config | 0 seconds | Transcripts (via yt-dlp), YouTube Music search/browse/charts/moods |
| **Tier 1** — API key | 30 seconds | + YouTube search, video details, comments (read), trending, channels, playlists (read) |
| **Tier 2** — OAuth | 2 minutes | + Everything: likes, comments (write), uploads, analytics, live streaming, YouTube Music library/playlists/history |

### Getting an API Key (Tier 1)

1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Create a project (or use an existing one)
3. Enable **YouTube Data API v3**
4. Create an API key
5. Run `axiomworks-youtube-mcp setup` and paste the key

### Setting Up OAuth (Tier 2)

1. In Google Cloud Console, create **OAuth 2.0 Client ID** (Desktop application)
2. Download the client secrets JSON file
3. Place it at `~/.config/axiomworks-youtube-mcp/client_secrets.json`
4. Run `axiomworks-youtube-mcp setup` and follow the OAuth flow

## Tools (68 total)

### YouTube Search & Discovery (3 tools)
| Tool | Description | Auth |
|------|-------------|------|
| `youtube_search` | Search for videos, channels, or playlists | API key |
| `youtube_trending` | Get trending videos by region/category | API key |
| `youtube_categories` | List available video categories | API key |

### Video Operations (8 tools)
| Tool | Description | Auth |
|------|-------------|------|
| `youtube_video_details` | Get metadata for one or more videos | API key |
| `youtube_video_transcript` | Get captions/transcript (via yt-dlp) | None |
| `youtube_video_rate` | Like, dislike, or remove rating | OAuth |
| `youtube_video_get_rating` | Get your rating on videos | OAuth |
| `youtube_video_upload` | Upload a video to YouTube | OAuth |
| `youtube_video_update` | Update video metadata | OAuth |
| `youtube_video_delete` | Delete a video | OAuth |
| `youtube_thumbnail_set` | Upload custom thumbnail | OAuth |

### Channel Operations (6 tools)
| Tool | Description | Auth |
|------|-------------|------|
| `youtube_channel_details` | Get channel info and stats | API key |
| `youtube_channel_videos` | List videos from a channel | API key |
| `youtube_channel_sections` | Get channel page sections | API key |
| `youtube_subscriptions_list` | List your subscriptions | OAuth |
| `youtube_subscribe` | Subscribe to a channel | OAuth |
| `youtube_unsubscribe` | Unsubscribe from a channel | OAuth |

### Playlist Operations (7 tools)
| Tool | Description | Auth |
|------|-------------|------|
| `youtube_playlist_details` | Get playlist metadata and items | API key |
| `youtube_playlist_create` | Create a new playlist | OAuth |
| `youtube_playlist_update` | Update playlist metadata | OAuth |
| `youtube_playlist_delete` | Delete a playlist | OAuth |
| `youtube_playlist_add_video` | Add a video to a playlist | OAuth |
| `youtube_playlist_remove_video` | Remove a video from a playlist | OAuth |
| `youtube_my_playlists` | List your playlists | OAuth |

### Comments (7 tools)
| Tool | Description | Auth |
|------|-------------|------|
| `youtube_comments_list` | Get comments on a video | API key |
| `youtube_comment_replies` | Get replies to a comment | API key |
| `youtube_comment_post` | Post a comment on a video | OAuth |
| `youtube_comment_reply` | Reply to a comment | OAuth |
| `youtube_comment_update` | Edit a comment | OAuth |
| `youtube_comment_delete` | Delete a comment | OAuth |
| `youtube_comment_moderate` | Set moderation status | OAuth |

### Analytics (5 tools)
| Tool | Description | Auth |
|------|-------------|------|
| `youtube_analytics_query` | Flexible analytics with dimensions/metrics | OAuth |
| `youtube_analytics_video` | Performance metrics for a specific video | OAuth |
| `youtube_analytics_top_videos` | Top-performing videos by metric | OAuth |
| `youtube_analytics_demographics` | Audience age, gender, geography | OAuth |
| `youtube_analytics_revenue` | Revenue and monetization metrics | OAuth |

### Live Streaming (3 tools)
| Tool | Description | Auth |
|------|-------------|------|
| `youtube_live_broadcasts` | List live broadcasts | OAuth |
| `youtube_live_chat_messages` | Read live chat messages | OAuth |
| `youtube_live_chat_send` | Send a message to live chat | OAuth |

### YouTube Music — Search & Browse (11 tools)
| Tool | Description | Auth |
|------|-------------|------|
| `ytmusic_search` | Search songs, albums, artists, playlists | None |
| `ytmusic_get_artist` | Artist page: bio, top songs, albums | None |
| `ytmusic_get_album` | Album details and track listing | None |
| `ytmusic_get_song` | Full song metadata | None |
| `ytmusic_get_lyrics` | Song lyrics | None |
| `ytmusic_get_watch_playlist` | Radio/up-next queue for a song | None |
| `ytmusic_home` | Personalized recommendations | OAuth |
| `ytmusic_charts` | Music charts by country | None |
| `ytmusic_moods` | Browse mood/genre categories | None |
| `ytmusic_mood_playlists` | Playlists for a mood/genre | None |
| `ytmusic_new_releases` | New music releases | None |

### YouTube Music — Library (9 tools)
| Tool | Description | Auth |
|------|-------------|------|
| `ytmusic_library_playlists` | Your music playlists | OAuth |
| `ytmusic_library_songs` | Your saved songs | OAuth |
| `ytmusic_library_albums` | Your saved albums | OAuth |
| `ytmusic_library_artists` | Your followed artists | OAuth |
| `ytmusic_liked_songs` | Your liked songs | OAuth |
| `ytmusic_history` | Listening history | OAuth |
| `ytmusic_rate_song` | Like/dislike a song | OAuth |
| `ytmusic_subscribe_artist` | Follow an artist | OAuth |
| `ytmusic_unsubscribe_artist` | Unfollow an artist | OAuth |

### YouTube Music — Playlists (6 tools)
| Tool | Description | Auth |
|------|-------------|------|
| `ytmusic_playlist_details` | Get playlist tracks and metadata | None/OAuth |
| `ytmusic_playlist_create` | Create a playlist | OAuth |
| `ytmusic_playlist_edit` | Edit playlist metadata | OAuth |
| `ytmusic_playlist_delete` | Delete a playlist | OAuth |
| `ytmusic_playlist_add_items` | Add songs to a playlist | OAuth |
| `ytmusic_playlist_remove_items` | Remove songs from a playlist | OAuth |

### YouTube Music — Podcasts (3 tools)
| Tool | Description | Auth |
|------|-------------|------|
| `ytmusic_get_podcast` | Podcast details and episodes | None |
| `ytmusic_get_episode` | Episode details | None |
| `ytmusic_get_channel` | Podcast channel page | None |

## Quota Management

The YouTube Data API has a **10,000 units/day** quota. This server includes built-in quota tracking:

| Operation | Cost | Daily Limit |
|-----------|------|-------------|
| Search | 100 units | ~100 searches |
| Read (details, comments, etc.) | 1 unit | ~10,000 reads |
| Write (comment, like, playlist edit) | 50 units | ~200 writes |
| Video upload | 1,600 units | ~6 uploads |

- Warnings at 80% usage (8,000 units)
- Errors at 100% to prevent failed API calls
- Quota resets daily at midnight Pacific Time
- YouTube Music tools use a separate internal API and are **not** subject to this quota

## Response Caching

Repeated queries are served from a local SQLite cache to reduce quota usage:

| Category | Cache Duration |
|----------|---------------|
| Search results | 5 minutes |
| Video details | 15 minutes |
| Channel info | 1 hour |
| Trending | 30 minutes |
| Comments | 5 minutes |
| Analytics | 1 hour |
| Music browse | 30 minutes |
| Music library | 5 minutes |

## API Gaps

Some YouTube features are not available through any official API. See [API_GAPS.md](API_GAPS.md) for a comprehensive list of limitations and our recommendations to YouTube for improvement.

Key gaps: no watch history API, no YouTube Shorts-specific endpoints, no YouTube Music official API, no playback control.

## Development

```bash
# Clone
git clone https://github.com/axiomworks-ai/axiomworks-youtube-mcp.git
cd axiomworks-youtube-mcp

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check src/

# Type check
mypy src/
```

## Architecture

```
src/axiomworks_youtube_mcp/
├── server.py          # MCP server + 68 tool definitions
├── config.py          # Configuration and auth tier management
├── cli.py             # CLI: setup, status, run, version
├── clients/
│   ├── youtube.py     # YouTube Data API v3 client
│   ├── ytmusic.py     # YouTube Music client (ytmusicapi)
│   ├── analytics.py   # YouTube Analytics API client
│   └── live.py        # YouTube Live Streaming client
└── utils/
    ├── cache.py       # Response caching (SQLite)
    └── quota.py       # Daily quota tracking and warnings
```

## Comparison

| Feature | This Server | ZubeidHendricks (472★) | kirbah (npm) | anaisbetts (507★) |
|---------|:-----------:|:----------------------:|:------------:|:-----------------:|
| YouTube Search | Yes | Yes | Yes | No |
| Video Details | Yes | Yes | Yes | No |
| Transcripts | Yes | No | Yes | Yes (only feature) |
| Comments (read) | Yes | No | No | No |
| Comments (write) | Yes | No | No | No |
| Playlists CRUD | Yes | Read-only | Read-only | No |
| Subscriptions | Yes | No | No | No |
| Video Upload | Yes | No | No | No |
| Analytics | Yes | No | No | No |
| Live Streaming | Yes | No | No | No |
| **YouTube Music** | **Yes** | No | No | No |
| Music Library | Yes | No | No | No |
| Music Playlists | Yes | No | No | No |
| Music Podcasts | Yes | No | No | No |
| Quota Tracking | Yes | No | No | No |
| Response Cache | Yes | No | No | No |
| **Total Tools** | **68** | 10 | 9 | 1 |

## License

[Apache License 2.0](LICENSE) — Free to use, modify, and distribute. Attribution required.

Copyright 2026 [Axiom Works AI](https://axiomworks.ai)

## Contributing

Contributions are welcome! Please see our contributing guidelines (coming soon).

Areas where help is especially valued:
- Additional YouTube Music features via [ytmusicapi](https://github.com/sigma67/ytmusicapi) upstream contributions
- Test coverage
- Documentation and examples
- Integration guides for different MCP clients
