"""Tests for the configuration module."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from axiomworks_youtube_mcp.config import (
    AuthTier,
    ServerConfig,
    ensure_config_dir,
    load_config,
    save_api_key,
)


class TestAuthTier:
    def test_zero_tier_values(self):
        assert AuthTier.ZERO.value == 0
        assert AuthTier.API_KEY.value == 1
        assert AuthTier.OAUTH.value == 2

    def test_tier_ordering(self):
        assert AuthTier.ZERO.value < AuthTier.API_KEY.value < AuthTier.OAUTH.value


class TestServerConfig:
    def test_default_config_is_zero_tier(self):
        config = ServerConfig()
        assert config.auth_tier == AuthTier.ZERO
        assert config.api_key is None
        assert config.google_oauth_credentials is None
        assert config.ytmusic_auth_path is None

    def test_api_key_sets_tier_1(self):
        config = ServerConfig(api_key="test-key-123")
        assert config.auth_tier == AuthTier.API_KEY

    def test_oauth_sets_tier_2(self):
        config = ServerConfig(google_oauth_credentials={"token": "abc"})
        assert config.auth_tier == AuthTier.OAUTH

    def test_ytmusic_auth_sets_tier_2(self):
        config = ServerConfig(ytmusic_auth_path=Path("/tmp/auth.json"))
        assert config.auth_tier == AuthTier.OAUTH

    def test_oauth_overrides_api_key(self):
        config = ServerConfig(
            api_key="test-key",
            google_oauth_credentials={"token": "abc"},
        )
        assert config.auth_tier == AuthTier.OAUTH

    def test_available_tool_count_zero(self):
        config = ServerConfig()
        assert config.available_tool_count == 14

    def test_available_tool_count_api_key(self):
        config = ServerConfig(api_key="key")
        assert config.available_tool_count == 31

    def test_available_tool_count_oauth(self):
        config = ServerConfig(google_oauth_credentials={"token": "t"})
        assert config.available_tool_count == 68

    def test_default_quota(self):
        config = ServerConfig()
        assert config.quota_daily_limit == 10_000
        assert config.quota_used_today == 0

    def test_cache_defaults(self):
        config = ServerConfig()
        assert config.cache_enabled is True
        assert config.cache_ttl_seconds == 300


class TestConfigPersistence:
    def test_ensure_config_dir_creates_directory(self, tmp_path):
        test_dir = tmp_path / ".config" / "axiomworks-youtube-mcp"
        with patch("axiomworks_youtube_mcp.config.CONFIG_DIR", test_dir):
            result = ensure_config_dir()
            assert result == test_dir
            assert test_dir.exists()

    def test_load_config_empty_returns_defaults(self, tmp_path):
        test_dir = tmp_path / ".config" / "axiomworks-youtube-mcp"
        test_dir.mkdir(parents=True)
        with (
            patch("axiomworks_youtube_mcp.config.API_KEY_PATH", test_dir / "api-key.txt"),
            patch("axiomworks_youtube_mcp.config.GOOGLE_OAUTH_PATH", test_dir / "oauth.json"),
            patch("axiomworks_youtube_mcp.config.YTMUSIC_OAUTH_PATH", test_dir / "ytmusic.json"),
        ):
            config = load_config()
            assert config.auth_tier == AuthTier.ZERO

    def test_save_and_load_api_key(self, tmp_path):
        test_dir = tmp_path / ".config" / "axiomworks-youtube-mcp"
        test_dir.mkdir(parents=True)
        key_path = test_dir / "api-key.txt"
        with (
            patch("axiomworks_youtube_mcp.config.CONFIG_DIR", test_dir),
            patch("axiomworks_youtube_mcp.config.API_KEY_PATH", key_path),
            patch("axiomworks_youtube_mcp.config.GOOGLE_OAUTH_PATH", test_dir / "oauth.json"),
            patch("axiomworks_youtube_mcp.config.YTMUSIC_OAUTH_PATH", test_dir / "ytmusic.json"),
        ):
            save_api_key("AIzaSyTest123")
            config = load_config()
            assert config.api_key == "AIzaSyTest123"
            assert config.auth_tier == AuthTier.API_KEY
