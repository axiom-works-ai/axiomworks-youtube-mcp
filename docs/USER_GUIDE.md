# YouTube + YouTube Music MCP — User Guide

## What You Can Do

This MCP server gives your AI assistant full access to YouTube and YouTube Music. Here's what that means in practice.

---

## For YouTube Viewers

### "What should I watch?"

Ask your AI to search YouTube, check trending videos, or find content from your favorite creators:

> "Find me the best Python tutorials published this month"
> "What's trending on YouTube right now in tech?"
> "Show me the latest videos from MKBHD"

**Tools used**: `youtube_search`, `youtube_trending`, `youtube_channel_videos`

### "What did they say in that video?"

Get transcripts from any video — great for summarizing long content or searching for a specific point:

> "Get the transcript from this video and summarize the key points"
> "What did the speaker say about pricing in this conference talk?"

**Tools used**: `youtube_video_transcript`

### "Help me manage my YouTube"

Like, subscribe, organize playlists:

> "Subscribe me to this channel"
> "Create a playlist called 'Watch This Week' and add these videos"
> "Like this video"

**Tools used**: `youtube_subscribe`, `youtube_playlist_create`, `youtube_playlist_add_video`, `youtube_video_rate`

---

## For YouTube Music Listeners

### "Play me something"

Search, browse charts, discover new music:

> "Search YouTube Music for lo-fi study beats"
> "What are the top songs in the US right now?"
> "Show me new music releases this week"
> "Find playlists for focus and concentration"

**Tools used**: `ytmusic_search`, `ytmusic_charts`, `ytmusic_new_releases`, `ytmusic_moods`, `ytmusic_mood_playlists`

### "Manage my music library"

Create playlists, manage liked songs, check listening history:

> "Create a playlist called 'Road Trip Mix' with these songs"
> "What have I been listening to lately?"
> "Show me my liked songs"
> "Add this song to my gym playlist"
> "Like this song"

**Tools used**: `ytmusic_playlist_create`, `ytmusic_playlist_add_items`, `ytmusic_history`, `ytmusic_liked_songs`, `ytmusic_rate_song`

### "Tell me about this artist"

Get deep info on any artist — bio, discography, top songs, related artists:

> "Tell me about Kendrick Lamar on YouTube Music"
> "What albums has Taylor Swift released?"
> "Get the lyrics for this song"

**Tools used**: `ytmusic_get_artist`, `ytmusic_get_album`, `ytmusic_get_lyrics`

---

## For YouTube Creators

### Content Management

Upload videos, update metadata, manage thumbnails:

> "Upload this video with the title 'Product Demo v2' as unlisted"
> "Update my latest video's description to include the new link"
> "Set this image as the thumbnail for my latest video"

**Tools used**: `youtube_video_upload`, `youtube_video_update`, `youtube_thumbnail_set`

### Community Engagement

Read and respond to comments, moderate discussions:

> "Show me the latest comments on my video"
> "Reply to this comment thanking them for the feedback"
> "Delete the spam comments on my latest upload"

**Tools used**: `youtube_comments_list`, `youtube_comment_post`, `youtube_comment_reply`, `youtube_comment_delete`, `youtube_comment_moderate`

### Analytics

Track video performance, understand your audience:

> "How is my latest video performing? Views, watch time, likes?"
> "What are my top 10 videos by views this month?"
> "Show me my audience demographics — age, gender, location"
> "What's my estimated revenue this quarter?"

**Tools used**: `youtube_analytics_video`, `youtube_analytics_top_videos`, `youtube_analytics_demographics`, `youtube_analytics_revenue`

### Live Streaming

Monitor and interact with live streams:

> "List my upcoming live broadcasts"
> "Read the latest chat messages from my live stream"
> "Send a message to my live chat"

**Tools used**: `youtube_live_broadcasts`, `youtube_live_chat_messages`, `youtube_live_chat_send`

---

## Creative Use Cases

### Research Assistant

> "Find the 5 most-viewed videos about quantum computing published this year, get their transcripts, and summarize the key findings across all of them"

Combines: `youtube_search` → `youtube_video_details` → `youtube_video_transcript` → AI summarization

### Podcast Discovery via YouTube Music

> "Find podcasts about AI and entrepreneurship on YouTube Music, and get the latest episodes"

Combines: `ytmusic_search` (filter: community_playlists) → `ytmusic_get_podcast` → `ytmusic_get_episode`

### Music Curation

> "Create a party playlist: search for top dance tracks from 2024-2026, pick the 20 best, and add them to a new playlist called 'Party Mix 2026'"

Combines: `ytmusic_search` → `ytmusic_playlist_create` → `ytmusic_playlist_add_items`

### Competitive Analysis (for Creators)

> "Compare my channel's recent performance to my competitor's: subscriber counts, recent video views, and posting frequency"

Combines: `youtube_channel_details` → `youtube_channel_videos` → `youtube_analytics_query`

### Daily Music Discovery

> "Every morning, check what's new on YouTube Music — new releases, trending charts, and any new songs from artists I follow. Send me a summary."

Combines: `ytmusic_new_releases` → `ytmusic_charts` → `ytmusic_library_artists` → notification

### Batch Transcript Analysis

> "Get transcripts from all videos in this playlist and create a study guide from the content"

Combines: `youtube_playlist_details` → `youtube_video_transcript` (loop) → AI synthesis

---

## Tips

### Quota Management

YouTube API has a 10,000 units/day quota. The MCP server tracks usage automatically:
- Searches cost 100 units each (~100 searches/day)
- Video details cost 1 unit (~10,000/day)
- Uploads cost 1,600 units (~6/day)
- YouTube Music tools use a separate internal API and are **not** subject to this quota

If you hit 80% usage, the server will warn you. At 100%, it blocks calls to prevent failed API requests.

### Authentication Tiers

You get more tools as you add credentials:

| Tier | Setup | What You Get |
|------|-------|-------------|
| Tier 0 | Nothing | Transcripts + YouTube Music browsing |
| Tier 1 | API key (30 seconds) | + YouTube search, details, comments |
| Tier 2 | OAuth (2 minutes) | + Everything: uploads, analytics, library management |

### YouTube Music vs YouTube

YouTube Music tools (`ytmusic_*`) use the `ytmusicapi` library which doesn't count against the YouTube API quota. You can search, browse, and manage your music library without worrying about quota limits.

YouTube tools (`youtube_*`) use the official Google API which has quota limits. The caching system helps — repeated queries within 5-30 minutes are served from cache without API calls.

---

## Need Help?

- [Setup guide](../README.md#setup)
- [Full tool reference](../README.md#tools-68-total)
- [API gaps we've documented](../API_GAPS.md)
- [File an issue](https://github.com/axiom-works-ai/axiomworks-youtube-mcp/issues)
