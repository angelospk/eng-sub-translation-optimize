"""Integration tests for subtitle optimizer."""

import os
import json
import pytest
from datetime import timedelta
from src.srt_processor import load_srt, save_srt, get_subtitle_stats, SubtitleEntry
from src.cps_optimizer import optimize_cps, reduce_lines, OptimizationConstraints
from src.llm_shortener import find_high_cps_segments, export_segments_json
from src.interjection_remover import RemoveInterjection, InterjectionRemoveContext
from src.interjections_en import INTERJECTIONS_EN, INTERJECTIONS_SKIP_EN


class TestIntegrationPipeline:
    """Integration tests for the full pipeline."""

    def test_full_pipeline_sample_srt(self, tmp_path):
        """Test full pipeline with sample SRT file."""
        # Load sample
        subs = load_srt('tests/fixtures/sample.srt')
        assert len(subs) > 0
        
        initial_stats = get_subtitle_stats(subs, target_cps=21)
        
        # Phase 1: Remove interjections
        remover = RemoveInterjection()
        cleaned = []
        for sub in subs:
            ctx = InterjectionRemoveContext(
                text=sub.text,
                interjections=INTERJECTIONS_EN,
                interjections_skip_if_starts_with=INTERJECTIONS_SKIP_EN,
            )
            new_text = remover.invoke(ctx)
            if new_text.strip():
                cleaned.append(SubtitleEntry(sub.index, sub.start, sub.end, new_text))
        
        # Some interjections should have been removed
        assert len(cleaned) <= len(subs)
        
        # Phase 1.5: Reduce lines
        for i, sub in enumerate(cleaned):
            if sub.line_count > 2:
                cleaned[i] = SubtitleEntry(
                    sub.index, sub.start, sub.end, reduce_lines(sub.text, 2)
                )
        
        # Phase 2: Optimize CPS
        constraints = OptimizationConstraints(max_chars=90, max_lines=2, max_duration=7.0)
        optimized = optimize_cps(cleaned, target_cps=21, constraints=constraints)
        
        # Should have merged some subtitles
        assert len(optimized) <= len(cleaned)
        
        # Phase 3: Find high-CPS segments
        segments = find_high_cps_segments(optimized, target_cps=21, min_reduction=6)
        
        # Export to JSON
        output_json = tmp_path / "high_cps.json"
        if segments:
            export_segments_json(segments, str(output_json))
            assert output_json.exists()
            
            # Verify JSON structure
            with open(output_json) as f:
                data = json.load(f)
            assert isinstance(data, list)
            if data:
                assert 'index' in data[0]
                assert 'original_text' in data[0]
        
        # Save output
        output_srt = tmp_path / "optimized.srt"
        save_srt(optimized, str(output_srt))
        assert output_srt.exists()
        
        # Reload and verify
        reloaded = load_srt(str(output_srt))
        assert len(reloaded) == len(optimized)
        
        # Final stats should be same or better
        final_stats = get_subtitle_stats(reloaded, target_cps=21)
        assert final_stats['total_count'] <= initial_stats['total_count']

    def test_interjection_integration(self):
        """Test interjection removal with real subtitle patterns."""
        remover = RemoveInterjection()
        
        # Test case from real subtitles: "Wow, um, you're just, this is..."
        ctx = InterjectionRemoveContext(
            text="Wow, um, you're just, this is...",
            interjections=INTERJECTIONS_EN,
            interjections_skip_if_starts_with=INTERJECTIONS_SKIP_EN,
        )
        result = remover.invoke(ctx)
        assert "um" not in result.lower()
        
        # Test dialog pattern
        ctx2 = InterjectionRemoveContext(
            text="- Oh, hey. Hi! You met Millie.\n- Hi, baby.",
            interjections=INTERJECTIONS_EN,
            interjections_skip_if_starts_with=INTERJECTIONS_SKIP_EN,
        )
        result2 = remover.invoke(ctx2)
        # "Oh" should be removed but dialog structure preserved
        assert "baby" in result2

    def test_cps_calculation_real_subtitles(self):
        """Test CPS calculation with real subtitle timing."""
        subs = load_srt('tests/fixtures/sample.srt')
        
        stats = get_subtitle_stats(subs, target_cps=21)
        
        # Verify reasonable CPS values
        assert 0 <= stats['min_cps'] <= 50
        assert stats['max_cps'] >= stats['min_cps']
        assert stats['avg_cps'] >= stats['min_cps']
        assert stats['avg_cps'] <= stats['max_cps']
