# YouTube API Gaps — Documented for Upstream Feedback

This document tracks features that the YouTube Data API v3, YouTube Analytics API, and YouTube Music ecosystem **do not support** but that users of AI assistants and MCP servers commonly need. These gaps limit what any YouTube MCP server can offer, regardless of implementation quality.

We publish this in the spirit of improving the ecosystem. If you work at Google/YouTube and want to discuss any of these, please open an issue.

## YouTube Data API v3

### No Watch History API
- **What's missing**: There is no endpoint to retrieve a user's watch history.
- **Impact**: AI assistants cannot answer "What did I watch last week?" or "Find that video I watched yesterday about [topic]."
- **Workaround**: None. Watch history is not exposed through any API, official or unofficial.
- **Severity**: High — this is one of the most commonly requested features for AI assistants.

### No Watch Later API
- **What's missing**: The "Watch Later" playlist exists but cannot be read or modified through the API. It was accessible historically but was removed.
- **Impact**: Cannot add videos to Watch Later or list what's queued.
- **Workaround**: Users can create a regular playlist called "Watch Later" as a substitute, but this doesn't integrate with YouTube's native Watch Later button.
- **Severity**: Medium

### No Liked Videos Playlist Write Access
- **What's missing**: The "Liked Videos" auto-playlist (LL) can be read but not directly managed as a playlist. You can like/unlike videos via `videos.rate`, but cannot reorder or bulk-manage liked videos.
- **Impact**: Limited playlist management for the most common user playlist.
- **Workaround**: Use `videos.rate` for individual like/unlike operations.
- **Severity**: Low

### YouTube Shorts — No Dedicated Endpoints
- **What's missing**: Shorts are regular videos with no API-level distinction. There is no way to:
  - Query specifically for Shorts
  - Filter search results to Shorts only
  - Get Shorts-specific analytics (Shorts vs. long-form performance)
  - Access Shorts-specific features (remix, audio, trending sounds)
- **Impact**: Cannot build Shorts-specific workflows or analytics.
- **Workaround**: Heuristic detection: filter by duration (<60s) and aspect ratio (9:16), or search for `#Shorts` in titles. Unreliable.
- **Severity**: High — Shorts is YouTube's fastest-growing format with no API parity.

### Community Posts — Not Accessible
- **What's missing**: Community tab posts (text, polls, images, quizzes) have no API endpoints.
- **Impact**: Cannot read, create, or interact with community posts. Major gap for channel management.
- **Workaround**: None.
- **Severity**: Medium

### Stories/Reels — Not Accessible
- **What's missing**: YouTube Stories (now discontinued for most creators) and Reels have no API.
- **Impact**: Minimal now that Stories are mostly deprecated.
- **Severity**: Low

### Notification Preferences — Not Accessible
- **What's missing**: Cannot manage notification bell settings (All/Personalized/None) for subscriptions.
- **Impact**: Cannot programmatically set notification preferences.
- **Workaround**: None.
- **Severity**: Low

### Quota Limits Are Restrictive for AI Use Cases
- **What's missing**: The 10,000 units/day default quota is designed for traditional web apps, not AI assistants that may make hundreds of queries per day. Search costs 100 units (limiting to 100 searches/day). There is no "personal use" tier with higher limits for authenticated users managing their own accounts.
- **Impact**: AI assistants must implement aggressive caching and quota management to avoid hitting limits.
- **Request**: A higher default quota for OAuth-authenticated personal use, or a "personal assistant" API tier.
- **Severity**: Medium — manageable with caching but limits functionality.

## YouTube Music

### No Official Public API
- **What's missing**: YouTube Music has no official public API. All integrations rely on `ytmusicapi`, an unofficial library that reverse-engineers YouTube Music's internal API.
- **Impact**: Integrations can break without notice when YouTube Music changes their internal API. No guaranteed stability, no official documentation, no support.
- **Request**: An official YouTube Music API, even if read-only, would unlock an entire ecosystem of music management tools.
- **Severity**: Critical — the entire YouTube Music integration category depends on unofficial access.

### No Playback Control API
- **What's missing**: Neither YouTube nor YouTube Music expose playback control (play, pause, skip, volume, seek) through any API. The Cast protocol can control Chromecast devices, but there's no API for controlling playback on the user's current device.
- **Impact**: AI assistants cannot say "play this song" and have it actually play. They can only queue songs or open URLs.
- **Workaround**: Open YouTube/YouTube Music URLs in the browser. Use Cast protocol for Chromecast devices.
- **Severity**: High — "play music" is one of the most natural AI assistant commands.

### No Real-Time "Now Playing" API
- **What's missing**: No way to know what the user is currently listening to in real-time.
- **Impact**: Cannot provide contextual suggestions ("since you're listening to jazz, here are similar artists") or log listening activity.
- **Workaround**: `get_history()` via ytmusicapi shows recent listens, but with a delay.
- **Severity**: Medium

### No Radio Station Management
- **What's missing**: YouTube Music radio stations (auto-generated based on songs/artists) cannot be created, saved, or managed through any API.
- **Impact**: Cannot programmatically create radio stations or save favorite mixes.
- **Workaround**: Use `get_watch_playlist()` to get the auto-generated queue for a song, which approximates radio behavior.
- **Severity**: Low

### No Collaborative Playlist Support
- **What's missing**: YouTube Music collaborative playlists cannot be managed (add/remove collaborators, set permissions) through the API.
- **Impact**: Cannot build shared playlist workflows.
- **Workaround**: None.
- **Severity**: Low

## YouTube Analytics API

### No Real-Time Analytics
- **What's missing**: Analytics data has a 2-3 day processing delay. There is no real-time or near-real-time analytics endpoint.
- **Impact**: Cannot answer "how is my video doing right now?" with current data.
- **Workaround**: Use the video's `statistics` from the Data API for real-time view/like counts (but no watch time, demographics, or traffic sources).
- **Severity**: Medium

### No Shorts-Specific Analytics
- **What's missing**: Analytics cannot be broken down by Shorts vs. long-form content.
- **Impact**: Creators cannot measure Shorts performance separately from their regular content.
- **Workaround**: Filter by video ID and manually classify which are Shorts.
- **Severity**: Medium

## YouTube Live Streaming API

### No Clips API
- **What's missing**: YouTube Clips (short highlights from live streams/videos) have no API for creation or management.
- **Impact**: Cannot programmatically create or manage clips.
- **Workaround**: None.
- **Severity**: Low

---

## How to Help

If you're a Google/YouTube developer or have access to the YouTube API feedback channels:

1. **Star this repository** — adoption numbers help make the case for API improvements.
2. **File feature requests** at the [YouTube Data API issue tracker](https://issuetracker.google.com/issues?q=componentid:186600).
3. **Reference this document** when filing requests — it provides concrete use cases from the MCP ecosystem.

The MCP ecosystem is growing rapidly (12,000+ servers as of March 2026). Better YouTube API coverage would benefit millions of users who interact with YouTube through AI assistants.

---

*Last updated: 2026-03-28*
*Maintained by: [Axiom Works AI](https://axiomworks.ai)*
