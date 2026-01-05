"""Tests for LLM shortener module."""

import json
import os
import pytest
from datetime import timedelta
from unittest.mock import patch, MagicMock

from src.srt_processor import SubtitleEntry
from src.llm_shortener import (
    HighCPSSegment,
    find_high_cps_segments,
    build_shortening_prompt,
    apply_shortened_text,
    export_segments_json,
    load_segments_json,
    shorten_with_llm,
)


class TestFindHighCPSSegments:
    """Tests for finding high-CPS segments."""

    def test_find_segments_basic(self):
        """Find segments exceeding CPS threshold."""
        subs = [
            SubtitleEntry(1, timedelta(seconds=0), timedelta(seconds=1), "Short"),  # 5 CPS
            SubtitleEntry(2, timedelta(seconds=2), timedelta(seconds=3), "This is a much longer text here"),  # 31 CPS
            SubtitleEntry(3, timedelta(seconds=4), timedelta(seconds=5), "OK"),  # 2 CPS
        ]
        
        segments = find_high_cps_segments(subs, target_cps=21, min_reduction=6)
        
        assert len(segments) == 1
        assert segments[0].index == 2
        assert segments[0].chars_to_reduce > 0

    def test_find_segments_none_high(self):
        """No segments if all under threshold."""
        subs = [
            SubtitleEntry(1, timedelta(seconds=0), timedelta(seconds=2), "Hello"),  # 2.5 CPS
            SubtitleEntry(2, timedelta(seconds=3), timedelta(seconds=5), "World"),  # 2.5 CPS
        ]
        
        segments = find_high_cps_segments(subs, target_cps=21, min_reduction=6)
        
        assert len(segments) == 0

    def test_find_segments_context(self):
        """Segments include context from surrounding subtitles."""
        subs = [
            SubtitleEntry(1, timedelta(seconds=0), timedelta(seconds=1), "Before text"),
            SubtitleEntry(2, timedelta(seconds=2), timedelta(seconds=2.5), "This is a super long subtitle text!!!"),  # 72 CPS
            SubtitleEntry(3, timedelta(seconds=3), timedelta(seconds=4), "After text"),
        ]
        
        segments = find_high_cps_segments(subs, target_cps=21, min_reduction=6)
        
        assert len(segments) == 1
        assert segments[0].context_before == "Before text"
        assert segments[0].context_after == "After text"

    def test_next_is_uppercase_detection(self):
        """Detect if next text starts with uppercase."""
        subs = [
            SubtitleEntry(1, timedelta(seconds=0), timedelta(seconds=0.5), "This is way too long for half second!"),  # 72 CPS
            SubtitleEntry(2, timedelta(seconds=1), timedelta(seconds=2), "Next starts lowercase"),
        ]
        
        segments = find_high_cps_segments(subs, target_cps=21, min_reduction=6)
        
        assert len(segments) == 1
        # "Next" starts with uppercase N
        assert segments[0].next_is_uppercase == True


class TestBuildShorteningPrompt:
    """Tests for prompt building."""

    def test_build_prompt_structure(self):
        """Prompt contains required elements."""
        segments = [
            HighCPSSegment(
                index=1,
                original_text="This is too long",
                current_cps=25,
                target_cps=21,
                chars_to_reduce=5,
            ),
        ]
        
        prompt = build_shortening_prompt(segments)
        
        assert "Index: 1" in prompt
        assert "This is too long" in prompt
        assert "JSON" in prompt
        assert "next_is_uppercase" in prompt


class TestApplyShortenedText:
    """Tests for applying LLM results."""

    def test_apply_shortened_text(self):
        """Apply shortened text back to subtitles."""
        subs = [
            SubtitleEntry(1, timedelta(seconds=0), timedelta(seconds=1), "Original text 1"),
            SubtitleEntry(2, timedelta(seconds=2), timedelta(seconds=3), "Original text 2"),
        ]
        
        segments = [
            HighCPSSegment(
                index=2,
                original_text="Original text 2",
                current_cps=25,
                target_cps=21,
                chars_to_reduce=5,
                shortened_text="Short v2",
            ),
        ]
        
        result = apply_shortened_text(subs, segments)
        
        assert result[0].text == "Original text 1"  # Unchanged
        assert result[1].text == "Short v2"  # Applied

    def test_apply_no_shortened_text(self):
        """Skip segments without shortened text."""
        subs = [
            SubtitleEntry(1, timedelta(seconds=0), timedelta(seconds=1), "Original"),
        ]
        
        segments = [
            HighCPSSegment(
                index=1,
                original_text="Original",
                current_cps=25,
                target_cps=21,
                chars_to_reduce=5,
                shortened_text=None,  # Not shortened
            ),
        ]
        
        result = apply_shortened_text(subs, segments)
        
        assert result[0].text == "Original"  # Unchanged


class TestExportLoadJSON:
    """Tests for JSON export/load."""

    def test_export_and_load(self, tmp_path):
        """Export segments to JSON and reload."""
        segments = [
            HighCPSSegment(
                index=5,
                original_text="Test text here",
                current_cps=30.5,
                target_cps=21,
                chars_to_reduce=8,
                context_before="Before",
                context_after="After",
                next_is_uppercase=False,
            ),
        ]
        
        json_path = tmp_path / "segments.json"
        export_segments_json(segments, str(json_path))
        
        # Verify file exists
        assert json_path.exists()
        
        # Load and verify
        loaded = load_segments_json(str(json_path))
        
        assert len(loaded) == 1
        assert loaded[0].index == 5
        assert loaded[0].original_text == "Test text here"
        assert loaded[0].current_cps == 30.5
        assert loaded[0].chars_to_reduce == 8
        assert loaded[0].next_is_uppercase == False

    def test_export_json_structure(self, tmp_path):
        """JSON has expected structure."""
        segments = [
            HighCPSSegment(
                index=1,
                original_text="Text",
                current_cps=25,
                target_cps=21,
                chars_to_reduce=5,
            ),
        ]
        
        json_path = tmp_path / "test.json"
        export_segments_json(segments, str(json_path))
        
        with open(json_path) as f:
            data = json.load(f)
        
        assert isinstance(data, list)
        assert len(data) == 1
        assert 'index' in data[0]
        assert 'original_text' in data[0]
        assert 'chars_to_reduce' in data[0]


class TestShortenWithLLM:
    """Tests for LLM integration (mocked)."""

    def test_shorten_with_llm_mocked(self):
        """Test LLM call with mocked response."""
        # Import here to patch correctly
        import src.llm_shortener as llm_module
        
        with patch.object(llm_module, 'shorten_with_llm') as mock_shorten:
            segments = [
                HighCPSSegment(
                    index=1,
                    original_text="This is too long",
                    current_cps=25,
                    target_cps=21,
                    chars_to_reduce=5,
                ),
            ]
            
            # Configure mock to set shortened_text
            def mock_impl(segs, api_key, model):
                for seg in segs:
                    seg.shortened_text = "Shortened"
                return segs
            
            mock_shorten.side_effect = mock_impl
            
            result = mock_shorten(segments, "fake_api_key", "gemini-2.5-flash")
            
            assert result[0].shortened_text == "Shortened"


# Optional: Integration test with real API (skipped by default)
@pytest.mark.skipif(
    not os.environ.get('GEMINI_API_KEY'),
    reason="GEMINI_API_KEY not set"
)
class TestLLMIntegration:
    """Integration tests with real Gemini API."""

    def test_real_llm_shortening(self):
        """Test actual LLM shortening with real API."""
        segments = [
            HighCPSSegment(
                index=1,
                original_text="I am absolutely certain that this text is significantly too long for comfort",
                current_cps=30,
                target_cps=21,
                chars_to_reduce=20,
                next_is_uppercase=True,
            ),
        ]
        
        api_key = os.environ.get('GEMINI_API_KEY')
        result = shorten_with_llm(segments, api_key, "gemini-2.5-flash")
        
        # Should have shortened text
        assert result[0].shortened_text is not None
        assert len(result[0].shortened_text) < len(result[0].original_text)
