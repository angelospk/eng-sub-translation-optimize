"""Tests for CPS optimizer module."""

import pytest
from datetime import timedelta
from src.srt_processor import SubtitleEntry
from src.cps_optimizer import (
    extend_timing,
    can_merge,
    merge_subtitles,
    reduce_lines,
    optimize_cps,
    OptimizationConstraints,
)


class TestExtendTiming:
    """Tests for timing extension."""

    def test_extend_timing_with_gap(self):
        """Extend timing when there's a gap."""
        sub = SubtitleEntry(1, timedelta(seconds=0), timedelta(seconds=1), "Test text here")
        next_sub = SubtitleEntry(2, timedelta(seconds=3), timedelta(seconds=5), "Next")
        
        # 14 chars in 1 second = 14 CPS, target is 21
        # With gap of 2 seconds, we can extend
        new_end = extend_timing(sub, next_sub, max_duration=7.0, min_gap=0.1)
        
        assert new_end > sub.end
        assert new_end < next_sub.start  # Should not overlap

    def test_extend_timing_no_gap(self):
        """Don't extend when no gap."""
        sub = SubtitleEntry(1, timedelta(seconds=0), timedelta(seconds=1), "Test")
        next_sub = SubtitleEntry(2, timedelta(seconds=1), timedelta(seconds=2), "Next")
        
        new_end = extend_timing(sub, next_sub, max_duration=7.0, min_gap=0.1)
        
        assert new_end == sub.end  # Unchanged

    def test_extend_timing_max_duration(self):
        """Respect max duration limit."""
        sub = SubtitleEntry(1, timedelta(seconds=0), timedelta(seconds=6), "Test")
        next_sub = SubtitleEntry(2, timedelta(seconds=10), timedelta(seconds=12), "Next")
        
        # Could extend to 10s but max is 7s
        new_end = extend_timing(sub, next_sub, max_duration=7.0, min_gap=0.1)
        
        assert (new_end - sub.start).total_seconds() <= 7.0


class TestCanMerge:
    """Tests for merge eligibility."""

    def test_can_merge_short_subtitles(self):
        """Can merge two short subtitles."""
        sub1 = SubtitleEntry(1, timedelta(seconds=0), timedelta(seconds=1), "Hello")
        sub2 = SubtitleEntry(2, timedelta(seconds=1), timedelta(seconds=2), "world")
        
        constraints = OptimizationConstraints(max_chars=90, max_lines=2, max_duration=7.0)
        assert can_merge(sub1, sub2, constraints) == True

    def test_cannot_merge_too_long(self):
        """Cannot merge when combined text too long."""
        sub1 = SubtitleEntry(1, timedelta(seconds=0), timedelta(seconds=1), "A" * 50)
        sub2 = SubtitleEntry(2, timedelta(seconds=1), timedelta(seconds=2), "B" * 50)
        
        constraints = OptimizationConstraints(max_chars=90, max_lines=2, max_duration=7.0)
        assert can_merge(sub1, sub2, constraints) == False

    def test_cannot_merge_too_many_lines(self):
        """Cannot merge when combined lines exceed max."""
        sub1 = SubtitleEntry(1, timedelta(seconds=0), timedelta(seconds=1), "Line one\nLine two")
        sub2 = SubtitleEntry(2, timedelta(seconds=1), timedelta(seconds=2), "Line three")
        
        constraints = OptimizationConstraints(max_chars=90, max_lines=2, max_duration=7.0)
        assert can_merge(sub1, sub2, constraints) == False


class TestMergeSubtitles:
    """Tests for subtitle merging."""

    def test_merge_simple(self):
        """Merge two simple subtitles."""
        sub1 = SubtitleEntry(1, timedelta(seconds=0), timedelta(seconds=1), "Hello")
        sub2 = SubtitleEntry(2, timedelta(seconds=1), timedelta(seconds=2), "world")
        
        merged = merge_subtitles(sub1, sub2)
        
        assert merged.start == sub1.start
        assert merged.end == sub2.end
        assert merged.text == "Hello\nworld"

    def test_merge_preserves_index(self):
        """Merged subtitle gets first index."""
        sub1 = SubtitleEntry(5, timedelta(seconds=0), timedelta(seconds=1), "A")
        sub2 = SubtitleEntry(6, timedelta(seconds=1), timedelta(seconds=2), "B")
        
        merged = merge_subtitles(sub1, sub2)
        
        assert merged.index == 5


class TestReduceLines:
    """Tests for line reduction."""

    def test_reduce_three_lines(self):
        """Reduce 3 lines to 2."""
        text = "Line one\nLine two\nLine three"
        reduced = reduce_lines(text, max_lines=2)
        
        assert reduced.count('\n') <= 1
        # All content should still be present
        assert "one" in reduced and "two" in reduced and "three" in reduced

    def test_keep_two_lines(self):
        """Two lines unchanged."""
        text = "Line one\nLine two"
        reduced = reduce_lines(text, max_lines=2)
        
        assert reduced == text

    def test_reduce_four_lines(self):
        """Reduce 4 lines to 2."""
        text = "A\nB\nC\nD"
        reduced = reduce_lines(text, max_lines=2)
        
        assert reduced.count('\n') <= 1


class TestOptimizeCPS:
    """Tests for main optimization loop."""

    def test_optimize_reduces_cps(self):
        """Optimization should reduce high CPS."""
        subs = [
            SubtitleEntry(1, timedelta(seconds=0), timedelta(seconds=1), "This is high CPS text"),  # 21 chars / 1s = 21 CPS
            SubtitleEntry(2, timedelta(seconds=5), timedelta(seconds=6), "More text"),  # Gap of 4s
        ]
        
        constraints = OptimizationConstraints(max_chars=90, max_lines=2, max_duration=7.0)
        optimized = optimize_cps(subs, target_cps=21, constraints=constraints)
        
        # First subtitle should have extended timing
        assert optimized[0].end > subs[0].end or optimized[0].duration > subs[0].duration
