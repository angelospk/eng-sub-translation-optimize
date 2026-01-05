"""Subtitle Optimizer - Core library package."""

from .interjection_remover import InterjectionRemoveContext, RemoveInterjection
from .interjections_en import INTERJECTIONS_EN, INTERJECTIONS_SKIP_EN
from .srt_processor import (
    SubtitleEntry,
    load_srt,
    save_srt,
    calculate_cps,
    get_subtitle_stats,
)
from .cps_optimizer import (
    OptimizationConstraints,
    extend_timing,
    can_merge,
    merge_subtitles,
    reduce_lines,
    optimize_cps,
)
from .llm_shortener import (
    HighCPSSegment,
    find_high_cps_segments,
    build_shortening_prompt,
    shorten_with_llm,
    apply_shortened_text,
    export_segments_json,
    load_segments_json,
)

__all__ = [
    # Interjection removal
    "InterjectionRemoveContext",
    "RemoveInterjection",
    "INTERJECTIONS_EN",
    "INTERJECTIONS_SKIP_EN",
    # SRT processing
    "SubtitleEntry",
    "load_srt",
    "save_srt",
    "calculate_cps",
    "get_subtitle_stats",
    # CPS optimization
    "OptimizationConstraints",
    "extend_timing",
    "can_merge",
    "merge_subtitles",
    "reduce_lines",
    "optimize_cps",
    # LLM shortening
    "HighCPSSegment",
    "find_high_cps_segments",
    "build_shortening_prompt",
    "shorten_with_llm",
    "apply_shortened_text",
    "export_segments_json",
    "load_segments_json",
]
