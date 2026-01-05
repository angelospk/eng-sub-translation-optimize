#!/usr/bin/env python3
"""Subtitle Optimizer CLI Tool.

Optimizes subtitle files by reducing CPS (Characters Per Second)
and preparing them for translation.

Usage:
    python subtitle_optimizer.py input.srt -o output.srt -j segments.json --max-cps 21
"""

import argparse
import os
import sys
from datetime import timedelta
from pathlib import Path


def load_env_file():
    """Load environment variables from .env file if it exists."""
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ.setdefault(key.strip(), value.strip())


# Load .env file before anything else
load_env_file()

from src.srt_processor import (
    load_srt,
    save_srt,
    calculate_cps,
    get_subtitle_stats,
    SubtitleEntry,
)
from src.cps_optimizer import (
    optimize_cps,
    reduce_lines,
    OptimizationConstraints,
)
from src.llm_shortener import (
    find_high_cps_segments,
    shorten_with_llm,
    apply_shortened_text,
    export_segments_json,
    load_segments_json,
)
from src.interjection_remover import (
    RemoveInterjection,
    InterjectionRemoveContext,
)
from src.interjections_en import INTERJECTIONS_EN, INTERJECTIONS_SKIP_EN


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Optimize subtitle files for CPS and translation.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s input.srt -o output.srt
  %(prog)s input.srt -j high_cps.json --max-cps 18
  %(prog)s input.srt --api-key $GEMINI_API_KEY
        """
    )
    
    parser.add_argument('input', help='Input SRT file')
    parser.add_argument('-o', '--output', help='Output SRT file (default: optimized_<input>)')
    parser.add_argument('-j', '--json', help='Export high-CPS segments to JSON')
    parser.add_argument('--apply-json', help='Apply shortened text from JSON file')
    parser.add_argument('--max-cps', type=float, default=21.0, help='Target CPS (default: 21)')
    parser.add_argument('--max-chars', type=int, default=90, help='Max chars per subtitle (default: 90)')
    parser.add_argument('--max-lines', type=int, default=2, help='Max lines per subtitle (default: 2)')
    parser.add_argument('--max-duration', type=float, default=7.0, help='Max duration in seconds (default: 7)')
    parser.add_argument('--api-key', default=os.environ.get('GEMINI_API_KEY'), 
                        help='Gemini API key (defaults to GEMINI_API_KEY env var or .env)')
    parser.add_argument('--model', default='gemini-2.5-flash', help='Gemini model (default: gemini-2.5-flash)')
    parser.add_argument('--simplify', action='store_true', help='Simplify for translation')
    parser.add_argument('--skip-interjections', action='store_true', help='Skip interjection removal')
    parser.add_argument('--skip-cps-opt', action='store_true', help='Skip CPS optimization')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    
    return parser.parse_args()


def print_stats(label: str, subtitles: list[SubtitleEntry], target_cps: float):
    """Print statistics about subtitle CPS."""
    stats = get_subtitle_stats(subtitles, target_cps)
    print(f"\n{label}:")
    print(f"  Total entries: {stats['total_count']}")
    print(f"  CPS range: {stats['min_cps']:.1f} - {stats['max_cps']:.1f}")
    print(f"  Average CPS: {stats['avg_cps']:.1f}")
    print(f"  High CPS (>{target_cps}): {stats['high_cps_count']} entries")


def phase1_remove_interjections(subtitles: list[SubtitleEntry], verbose: bool = False) -> list[SubtitleEntry]:
    """Phase 1: Remove interjections from subtitles."""
    if verbose:
        print("\n🔄 Phase 1: Removing interjections...")
    
    remover = RemoveInterjection()
    result = []
    removed_count = 0
    
    for sub in subtitles:
        context = InterjectionRemoveContext(
            text=sub.text,
            interjections=INTERJECTIONS_EN,
            interjections_skip_if_starts_with=INTERJECTIONS_SKIP_EN,
            only_separated_lines=False,
        )
        
        new_text = remover.invoke(context)
        
        if new_text != sub.text:
            removed_count += 1
        
        if new_text.strip():
            result.append(SubtitleEntry(
                index=sub.index,
                start=sub.start,
                end=sub.end,
                text=new_text
            ))
        # Skip empty subtitles after interjection removal
    
    if verbose:
        print(f"  Modified {removed_count} entries, removed {len(subtitles) - len(result)} empty entries")
    
    return result


def phase1_5_reduce_lines(subtitles: list[SubtitleEntry], max_lines: int = 2, verbose: bool = False) -> list[SubtitleEntry]:
    """Phase 1.5: Reduce subtitle lines to maximum."""
    if verbose:
        print(f"\n🔄 Phase 1.5: Reducing lines to max {max_lines}...")
    
    result = []
    reduced_count = 0
    
    for sub in subtitles:
        if sub.line_count > max_lines:
            new_text = reduce_lines(sub.text, max_lines)
            result.append(SubtitleEntry(
                index=sub.index,
                start=sub.start,
                end=sub.end,
                text=new_text
            ))
            reduced_count += 1
        else:
            result.append(sub)
    
    if verbose:
        print(f"  Reduced {reduced_count} entries")
    
    return result


def phase2_optimize_cps(
    subtitles: list[SubtitleEntry],
    target_cps: float,
    constraints: OptimizationConstraints,
    verbose: bool = False
) -> list[SubtitleEntry]:
    """Phase 2: Optimize CPS through timing and merging."""
    if verbose:
        print(f"\n🔄 Phase 2: Optimizing CPS (target: {target_cps})...")
    
    result = optimize_cps(subtitles, target_cps, constraints)
    
    if verbose:
        merged = len(subtitles) - len(result)
        print(f"  Merged {merged} subtitle pairs")
    
    return result


def phase3_find_high_cps(
    subtitles: list[SubtitleEntry],
    target_cps: float,
    min_reduction: int = 6,
    verbose: bool = False
):
    """Phase 3: Find segments that still need LLM shortening."""
    if verbose:
        print(f"\n🔄 Phase 3: Finding high-CPS segments...")
    
    segments = find_high_cps_segments(subtitles, target_cps, min_reduction)
    
    if verbose:
        print(f"  Found {len(segments)} segments needing LLM shortening")
    
    return segments


def phase4_llm_shortening(
    subtitles: list[SubtitleEntry],
    segments,
    api_key: str,
    model: str,
    verbose: bool = False
) -> list[SubtitleEntry]:
    """Phase 4: Use LLM to shorten high-CPS segments."""
    if verbose:
        print(f"\n🔄 Phase 4: LLM shortening with {model}...")
    
    try:
        shortened_segments = shorten_with_llm(segments, api_key, model)
        result = apply_shortened_text(subtitles, shortened_segments)
        
        applied = sum(1 for s in shortened_segments if s.shortened_text)
        if verbose:
            print(f"  Applied {applied} shortened segments")
        
        return result
    except Exception as e:
        if verbose:
            print(f"  ⚠️ LLM shortening failed: {e}")
        return subtitles


def reindex_subtitles(subtitles: list[SubtitleEntry]) -> list[SubtitleEntry]:
    """Re-index subtitles sequentially starting from 1."""
    return [
        SubtitleEntry(
            index=i,
            start=sub.start,
            end=sub.end,
            text=sub.text
        )
        for i, sub in enumerate(subtitles, 1)
    ]


def main():
    """Main entry point."""
    args = parse_args()
    
    # Check input file
    if not os.path.exists(args.input):
        print(f"Error: Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    
    # Load subtitles
    print(f"📂 Loading: {args.input}")
    subtitles = load_srt(args.input)
    print(f"  Loaded {len(subtitles)} subtitle entries")
    
    if args.verbose:
        print_stats("Initial statistics", subtitles, args.max_cps)
    
    # Handle apply-json mode
    if args.apply_json:
        print(f"\n📥 Applying shortened text from: {args.apply_json}")
        segments = load_segments_json(args.apply_json)
        subtitles = apply_shortened_text(subtitles, segments)
    else:
        # Create constraints
        constraints = OptimizationConstraints(
            max_chars=args.max_chars,
            max_lines=args.max_lines,
            max_duration=args.max_duration,
        )
        
        # Phase 1: Remove interjections
        if not args.skip_interjections:
            subtitles = phase1_remove_interjections(subtitles, args.verbose)
        
        # Phase 1.5: Reduce lines
        subtitles = phase1_5_reduce_lines(subtitles, args.max_lines, args.verbose)
        
        # Phase 2: Optimize CPS
        if not args.skip_cps_opt:
            subtitles = phase2_optimize_cps(subtitles, args.max_cps, constraints, args.verbose)
        
        # Phase 3: Find high-CPS segments
        segments = phase3_find_high_cps(subtitles, args.max_cps, verbose=args.verbose)
        
        # Export JSON if requested
        if args.json and segments:
            export_segments_json(segments, args.json)
            print(f"\n📤 Exported {len(segments)} high-CPS segments to: {args.json}")
        
        # Phase 4: LLM shortening if API key provided
        if args.api_key and segments:
            subtitles = phase4_llm_shortening(
                subtitles, segments, args.api_key, args.model, args.verbose
            )
    
    # Re-index subtitles
    subtitles = reindex_subtitles(subtitles)
    
    # Final statistics
    if args.verbose:
        print_stats("Final statistics", subtitles, args.max_cps)
    
    # Determine output path
    output_path = args.output
    if not output_path:
        base = os.path.basename(args.input)
        output_path = f"optimized_{base}"
    
    # Save output
    save_srt(subtitles, output_path)
    print(f"\n✅ Saved: {output_path} ({len(subtitles)} entries)")
    
    # Summary
    final_stats = get_subtitle_stats(subtitles, args.max_cps)
    if final_stats['high_cps_count'] > 0:
        print(f"⚠️  {final_stats['high_cps_count']} entries still exceed target CPS of {args.max_cps}")
        if not args.api_key and args.json:
            print(f"   Use LLM to shorten segments in {args.json}, then run:")
            print(f"   python subtitle_optimizer.py {output_path} --apply-json {args.json}")
    else:
        print(f"🎉 All entries meet target CPS of {args.max_cps}!")


if __name__ == '__main__':
    main()
