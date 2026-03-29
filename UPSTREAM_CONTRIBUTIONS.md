# Upstream Contributions — ytmusicapi

Axiom Works contributions to [sigma67/ytmusicapi](https://github.com/sigma67/ytmusicapi), the foundation of our YouTube Music integration.

## Repository Context
- **Version**: 1.11.5 (monthly releases)
- **Stars**: 2,564 / **Forks**: 285
- **Maintainer**: sigma67 (very responsive, merges PRs in 1-3 days)
- **Requirements**: Issue first, pytest tests, ruff lint, mypy strict, 95%+ coverage
- **Setup**: Uses `pdm` for deps, `pre-commit` for hooks

## Planned Contributions

### 1. Votes in `edit_playlist` (Issue #872) — PRIORITY
- **Status**: Maintainer-filed, labeled "good first issue" + "help wanted", previous PR was invalid
- **What**: Add `voting: bool | None` parameter to `edit_playlist()` to enable/disable voting on playlist items
- **Effort**: ~2 hours
- **Merge likelihood**: Very high — sigma67 is waiting for this

### 2. `get_song_credits` (Issue #883)
- **Status**: Maintainer confirmed "valid request". PR #884 exists but may stall on test failures
- **What**: New function to get song credits (producers, writers, engineers) via `MPTC` browseId prefix
- **Effort**: ~4 hours
- **Merge likelihood**: High — monitor PR #884, submit competing PR if it stalls

### 3. Validated Continuations for `get_playlist` (Issue #778)
- **Status**: Labeled "help wanted" + "good first issue", pattern exists in `get_library_songs`
- **What**: Add retry logic for large playlists that fail to return all tracks
- **Effort**: ~3 hours (port existing pattern)
- **Merge likelihood**: High — clear approach, no competing PRs

### 4. Async Scaffolding `YTMusicAsync` (Issue #850) — HIGH VISIBILITY
- **Status**: Maintainer explicitly approved approach, wants it broken into multiple PRs
- **What**: Create `YTMusicAsync` class with all method stubs raising `NotImplementedError`
- **Effort**: ~1 day for scaffolding, weeks for full implementation
- **Merge likelihood**: Medium-high — establishes Axiom Works as a major contributor

## Contribution Guidelines
- Always file/reference an issue before submitting a PR
- Run `pdm install && pre-commit install` for development setup
- Every new function needs tests in `tests/`
- Pass `ruff check`, `ruff format`, and `mypy --strict`
- Keep PRs small and focused (one feature per PR)

## Attribution
Contributions should be made from the `axiomworks-ai` GitHub org account with clear attribution to Axiom Works AI.
