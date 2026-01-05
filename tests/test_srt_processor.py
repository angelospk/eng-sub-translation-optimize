"""Tests for SRT processing module."""

import os
import pytest
from datetime import timedelta
from src.srt_processor import (
    load_srt,
    save_srt,
    calculate_cps,
    get_subtitle_stats,
    SubtitleEntry,
)


class TestCalculateCPS:
    """Tests for CPS calculation."""

    def test_basic_cps_calculation(self):
        """Calculate CPS for simple subtitle."""
        # 10 characters in 2 seconds = 5 CPS
        sub = SubtitleEntry(
            index=1,
            start=timedelta(seconds=0),
            end=timedelta(seconds=2),
            text="Hello test"
        )
        assert calculate_cps(sub) == 5.0

    def test_cps_excludes_newlines(self):
        """CPS calculation should count actual characters, not newlines."""
        # "Hello\nworld" = 10 characters (excluding newline)
        sub = SubtitleEntry(
            index=1,
            start=timedelta(seconds=0),
            end=timedelta(seconds=2),
            text="Hello\nworld"
        )
        assert calculate_cps(sub) == 5.0

    def test_cps_zero_duration(self):
        """Handle zero duration gracefully."""
        sub = SubtitleEntry(
            index=1,
            start=timedelta(seconds=0),
            end=timedelta(seconds=0),
            text="Test"
        )
        # Should return infinity or max CPS
        assert calculate_cps(sub) == float('inf')

    def test_cps_high_value(self):
        """High CPS for fast subtitle."""
        # 41 characters in 1 second = 41 CPS
        sub = SubtitleEntry(
            index=1,
            start=timedelta(seconds=0),
            end=timedelta(seconds=1),
            text="This is a very long subtitle text sample!"
        )
        assert calculate_cps(sub) == 41.0


class TestSubtitleStats:
    """Tests for subtitle statistics."""

    def test_stats_basic(self):
        """Get basic statistics."""
        subs = [
            SubtitleEntry(1, timedelta(seconds=0), timedelta(seconds=2), "Hi there"),  # 8 chars / 2s = 4 CPS
            SubtitleEntry(2, timedelta(seconds=3), timedelta(seconds=4), "Hello world test"),  # 16 chars / 1s = 16 CPS
            SubtitleEntry(3, timedelta(seconds=5), timedelta(seconds=7), "Test this now please"),  # 20 chars / 2s = 10 CPS
        ]
        stats = get_subtitle_stats(subs, target_cps=15)
        
        assert stats['min_cps'] == 4.0
        assert stats['max_cps'] == 16.0
        assert stats['avg_cps'] == 10.0
        assert stats['high_cps_count'] == 1  # Only the 16 CPS one exceeds 15

    def test_stats_empty_list(self):
        """Handle empty subtitle list."""
        stats = get_subtitle_stats([], target_cps=21)
        assert stats['min_cps'] == 0
        assert stats['max_cps'] == 0
        assert stats['avg_cps'] == 0
        assert stats['high_cps_count'] == 0


class TestLoadSaveSRT:
    """Tests for SRT file I/O."""

    def test_load_sample_srt(self):
        """Load sample SRT file."""
        subs = load_srt('tests/fixtures/sample.srt')
        assert len(subs) > 0
        assert subs[0].index == 1
        assert subs[0].text.strip() != ""

    def test_save_and_reload(self, tmp_path):
        """Save SRT and reload it."""
        subs = [
            SubtitleEntry(
                index=1,
                start=timedelta(seconds=1),
                end=timedelta(seconds=3),
                text="Hello world"
            ),
            SubtitleEntry(
                index=2,
                start=timedelta(seconds=4),
                end=timedelta(seconds=6),
                text="Test subtitle"
            ),
        ]
        
        output_path = tmp_path / "test_output.srt"
        save_srt(subs, str(output_path))
        
        # Reload and verify
        reloaded = load_srt(str(output_path))
        assert len(reloaded) == 2
        assert reloaded[0].text == "Hello world"
        assert reloaded[1].text == "Test subtitle"
