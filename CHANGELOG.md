# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-03-29

### Added
- Initial release with 68 MCP tools across 11 groups
- **YouTube Search & Discovery** (3 tools): search, trending, categories
- **Video Operations** (8 tools): details, transcripts, rate, upload, update, delete, thumbnails
- **Channel Operations** (6 tools): details, videos, sections, subscriptions
- **Playlist CRUD** (7 tools): full create/read/update/delete
- **Comments** (7 tools): read, post, reply, update, delete, moderate
- **Analytics** (5 tools): flexible queries, video metrics, demographics, revenue
- **Live Streaming** (3 tools): broadcasts, chat read, chat send
- **YouTube Music Search & Browse** (11 tools): search, artists, albums, songs, lyrics, charts
- **YouTube Music Library** (9 tools): playlists, songs, albums, artists, history, ratings
- **YouTube Music Playlists** (6 tools): full CRUD
- **YouTube Music Podcasts** (3 tools): podcasts, episodes, channels
- Tiered authentication: Tier 0 (zero config), Tier 1 (API key), Tier 2 (OAuth)
- Response caching with category-specific TTLs (SQLite-backed)
- Daily quota tracking with 80%/100% thresholds
- CLI: `setup`, `status`, `run`, `version` commands
- Comprehensive documentation: README, USER_GUIDE, API_GAPS, UPSTREAM_CONTRIBUTIONS
