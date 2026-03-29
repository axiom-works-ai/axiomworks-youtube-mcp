"""Tests for the quota tracking module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.fixture
def temp_quota(tmp_path):
    """Use a temporary directory for quota database."""
    quota_dir = tmp_path / "config"
    quota_dir.mkdir()
    quota_db = quota_dir / "quota.db"

    import axiomworks_youtube_mcp.utils.quota as quota_mod

    with patch.object(quota_mod, "QUOTA_DB_PATH", quota_db):
        yield quota_mod


class TestQuotaTracking:
    def test_initial_remaining_is_full(self, temp_quota):
        result = temp_quota.get_remaining_quota()
        assert result["remaining"] == 10_000
        assert result["used_today"] == 0

    def test_track_usage_reduces_remaining(self, temp_quota):
        temp_quota.track_usage("search", 100)
        result = temp_quota.get_remaining_quota()
        assert result["remaining"] == 9_900
        assert result["used_today"] == 100

    def test_multiple_usages_accumulate(self, temp_quota):
        temp_quota.track_usage("search", 100)
        temp_quota.track_usage("search", 100)
        temp_quota.track_usage("read", 1)
        result = temp_quota.get_remaining_quota()
        assert result["remaining"] == 9_799
        assert result["used_today"] == 201

    def test_check_quota_passes_when_available(self, temp_quota):
        # Should not raise when quota is available
        result = temp_quota.check_quota_before_call(100)
        # Result may be None or a string — just verify no exception

    def test_check_quota_blocks_at_100_percent(self, temp_quota):
        # Use all 10000 units
        temp_quota.track_usage("bulk", 10_000)
        with pytest.raises((ValueError, Exception)):
            temp_quota.check_quota_before_call(100)
