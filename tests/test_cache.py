"""Tests for the response caching module."""

from __future__ import annotations

import time
from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.fixture
def temp_cache(tmp_path):
    """Use a temporary directory for cache database."""
    cache_dir = tmp_path / "config"
    cache_dir.mkdir()
    cache_db = cache_dir / "cache.db"
    with patch("axiomworks_youtube_mcp.utils.cache.CONFIG_DIR", cache_dir):
        with patch("axiomworks_youtube_mcp.utils.cache.CACHE_DB_PATH", cache_db):
            # Reset the module-level connection
            import axiomworks_youtube_mcp.utils.cache as cache_mod
            cache_mod._db = None
            yield cache_mod
            if cache_mod._db:
                cache_mod._db.close()
                cache_mod._db = None


class TestCacheTTL:
    def test_ttl_values_exist(self):
        from axiomworks_youtube_mcp.utils.cache import TTL
        assert "search" in TTL
        assert "video_details" in TTL
        assert "channel" in TTL
        assert "default" in TTL

    def test_search_ttl_is_5_minutes(self):
        from axiomworks_youtube_mcp.utils.cache import TTL
        assert TTL["search"] == 300

    def test_channel_ttl_is_1_hour(self):
        from axiomworks_youtube_mcp.utils.cache import TTL
        assert TTL["channel"] == 3600


class TestCacheOperations:
    def test_cache_miss_returns_none(self, temp_cache):
        result = temp_cache.get_cached("youtube_search", {"query": "test"}, "search")
        assert result is None

    def test_set_and_get_cached(self, temp_cache):
        params = {"query": "python tutorials"}
        temp_cache.set_cached("youtube_search", params, '{"results": []}', "search")
        result = temp_cache.get_cached("youtube_search", params, "search")
        assert result == '{"results": []}'

    def test_different_params_different_cache(self, temp_cache):
        params1 = {"query": "python"}
        params2 = {"query": "rust"}
        temp_cache.set_cached("youtube_search", params1, '{"results": ["py"]}', "search")
        temp_cache.set_cached("youtube_search", params2, '{"results": ["rs"]}', "search")

        assert temp_cache.get_cached("youtube_search", params1, "search") == '{"results": ["py"]}'
        assert temp_cache.get_cached("youtube_search", params2, "search") == '{"results": ["rs"]}'

    def test_none_params_excluded_from_key(self, temp_cache):
        params1 = {"query": "test", "filter": None}
        params2 = {"query": "test"}
        temp_cache.set_cached("ytmusic_search", params1, '"data"', "default")
        # Should match since None params are excluded
        result = temp_cache.get_cached("ytmusic_search", params2, "default")
        assert result == '"data"'

    def test_invalidate_clears_cache(self, temp_cache):
        temp_cache.set_cached("youtube_search", {"q": "a"}, '"a"', "search")
        temp_cache.set_cached("youtube_search", {"q": "b"}, '"b"', "search")
        count = temp_cache.invalidate()
        assert count == 2
        assert temp_cache.get_cached("youtube_search", {"q": "a"}, "search") is None

    def test_cleanup_expired(self, temp_cache):
        # Set a cached item with a very short TTL
        with patch.dict(temp_cache.TTL, {"test": 0}):
            temp_cache.set_cached("test_tool", {"x": 1}, '"old"', "test")
        # It should be expired immediately
        time.sleep(0.1)
        count = temp_cache.cleanup_expired()
        assert count >= 1

    def test_get_stats(self, temp_cache):
        temp_cache.set_cached("tool1", {"a": 1}, '"x"', "search")
        temp_cache.set_cached("tool2", {"b": 2}, '"y"', "channel")
        stats = temp_cache.get_stats()
        assert stats["total_entries"] == 2
        assert "search" in stats["by_category"]
        assert "channel" in stats["by_category"]
