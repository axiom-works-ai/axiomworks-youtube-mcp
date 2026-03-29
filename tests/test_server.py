"""Tests for the MCP server tool registration."""

from __future__ import annotations


def test_server_imports():
    """Server module should import without errors."""
    from axiomworks_youtube_mcp import server
    assert server.mcp is not None


def test_server_name():
    """Server should have correct name."""
    from axiomworks_youtube_mcp.server import mcp
    assert mcp.name == "axiomworks-youtube-mcp"


def test_get_config_returns_config():
    """get_config should return a ServerConfig instance."""
    from axiomworks_youtube_mcp.server import get_config
    from axiomworks_youtube_mcp.config import ServerConfig
    config = get_config()
    assert isinstance(config, ServerConfig)


def test_require_api_key_raises_without_key():
    """require_api_key should raise ValueError when no key is set."""
    import pytest
    from axiomworks_youtube_mcp.server import require_api_key
    from axiomworks_youtube_mcp.config import ServerConfig
    from unittest.mock import patch

    with patch("axiomworks_youtube_mcp.server._config", ServerConfig()):
        with pytest.raises(ValueError, match="YouTube API key required"):
            require_api_key()


def test_require_oauth_raises_without_credentials():
    """require_oauth should raise ValueError when no OAuth is set."""
    import pytest
    from axiomworks_youtube_mcp.server import require_oauth
    from axiomworks_youtube_mcp.config import ServerConfig
    from unittest.mock import patch

    with patch("axiomworks_youtube_mcp.server._config", ServerConfig()):
        with pytest.raises(ValueError, match="Google OAuth required"):
            require_oauth()
