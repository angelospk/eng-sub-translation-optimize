"""CPS optimization module.

Handles timing extension, subtitle merging, and line reduction.
"""

from dataclasses import dataclass
from datetime import timedelta
from typing import Optional

from .srt_processor import SubtitleEntry, calculate_cps


@dataclass
class OptimizationConstraints:
    """Constraints for subtitle optimization."""
    max_chars: int = 90
    max_lines: int = 2
    max_duration: float = 7.0
    min_duration: float = 0.833  # 5/6 second
    min_gap: float = 0.1  # Minimum gap between subtitles


def extend_timing(
    subtitle: SubtitleEntry,
    next_subtitle: Optional[SubtitleEntry],
    max_duration: float = 7.0,
    min_gap: float = 0.1
) -> timedelta:
    """Calculate extended end time for a subtitle.
    
    Args:
        subtitle: The subtitle to extend.
        next_subtitle: The following subtitle (None if last).
        max_duration: Maximum duration allowed.
        min_gap: Minimum gap to maintain before next subtitle.
        
    Returns:
        New end time (may be unchanged if no extension possible).
    """
    current_end = subtitle.end
    current_duration = subtitle.duration
    
    # Already at max duration
    if current_duration >= max_duration:
        return current_end
    
    # Calculate maximum possible end time
    max_end_by_duration = subtitle.start + timedelta(seconds=max_duration)
    
    if next_subtitle is None:
        # Last subtitle - extend to max duration
        return max_end_by_duration
    
    # Calculate available gap
    gap = (next_subtitle.start - current_end).total_seconds()
    
    if gap <= min_gap:
        # No room to extend
        return current_end
    
    # Extend up to next subtitle minus minimum gap, or max duration
    max_end_by_gap = next_subtitle.start - timedelta(seconds=min_gap)
    
    return min(max_end_by_duration, max_end_by_gap)


def can_merge(
    sub1: SubtitleEntry,
    sub2: SubtitleEntry,
    constraints: OptimizationConstraints
) -> bool:
    """Check if two subtitles can be merged.
    
    Args:
        sub1: First subtitle.
        sub2: Second subtitle (must follow sub1).
        constraints: Optimization constraints.
        
    Returns:
        True if subtitles can be merged.
    """
    # Check combined char count
    combined_chars = sub1.char_count + sub2.char_count
    if combined_chars > constraints.max_chars:
        return False
    
    # Check combined line count
    combined_lines = sub1.line_count + sub2.line_count
    if combined_lines > constraints.max_lines:
        return False
    
    # Check combined duration
    combined_duration = (sub2.end - sub1.start).total_seconds()
    if combined_duration > constraints.max_duration:
        return False
    
    return True


def merge_subtitles(sub1: SubtitleEntry, sub2: SubtitleEntry) -> SubtitleEntry:
    """Merge two adjacent subtitles into one.
    
    Args:
        sub1: First subtitle.
        sub2: Second subtitle.
        
    Returns:
        New merged subtitle.
    """
    merged_text = f"{sub1.text}\n{sub2.text}"
    
    return SubtitleEntry(
        index=sub1.index,
        start=sub1.start,
        end=sub2.end,
        text=merged_text
    )


def reduce_lines(text: str, max_lines: int = 2) -> str:
    """Reduce text to maximum number of lines.
    
    Args:
        text: Input text with newlines.
        max_lines: Maximum lines to keep.
        
    Returns:
        Text with at most max_lines lines.
    """
    lines = text.split('\n')
    
    if len(lines) <= max_lines:
        return text
    
    # Combine lines to reduce count
    # Strategy: combine shortest consecutive lines
    while len(lines) > max_lines:
        # Find the best pair to combine (shortest combined length)
        best_idx = 0
        best_len = float('inf')
        
        for i in range(len(lines) - 1):
            combined_len = len(lines[i]) + len(lines[i + 1])
            if combined_len < best_len:
                best_len = combined_len
                best_idx = i
        
        # Combine the pair
        lines[best_idx] = lines[best_idx] + ' ' + lines[best_idx + 1]
        lines.pop(best_idx + 1)
    
    return '\n'.join(lines)


def optimize_cps(
    subtitles: list[SubtitleEntry],
    target_cps: float = 21.0,
    constraints: Optional[OptimizationConstraints] = None
) -> list[SubtitleEntry]:
    """Optimize subtitles to reduce CPS.
    
    Applies timing extension and merging to reduce high CPS values.
    
    Args:
        subtitles: List of subtitle entries.
        target_cps: Target maximum CPS.
        constraints: Optimization constraints (uses defaults if None).
        
    Returns:
        Optimized list of subtitle entries.
    """
    if not subtitles:
        return []
    
    if constraints is None:
        constraints = OptimizationConstraints()
    
    result = []
    
    for i, sub in enumerate(subtitles):
        # Get next subtitle
        next_sub = subtitles[i + 1] if i + 1 < len(subtitles) else None
        
        # Check if CPS is too high
        current_cps = calculate_cps(sub)
        
        if current_cps > target_cps:
            # Try to extend timing
            new_end = extend_timing(sub, next_sub, constraints.max_duration, constraints.min_gap)
            
            if new_end > sub.end:
                sub = SubtitleEntry(
                    index=sub.index,
                    start=sub.start,
                    end=new_end,
                    text=sub.text
                )
        
        result.append(sub)
    
    # Second pass: try merging
    merged_result = []
    skip_next = False
    
    for i, sub in enumerate(result):
        if skip_next:
            skip_next = False
            continue
        
        if i + 1 < len(result):
            next_sub = result[i + 1]
            
            # Check if merging would help
            combined_cps = (sub.char_count + next_sub.char_count) / (next_sub.end - sub.start).total_seconds()
            
            if combined_cps <= target_cps and can_merge(sub, next_sub, constraints):
                merged = merge_subtitles(sub, next_sub)
                merged_result.append(merged)
                skip_next = True
                continue
        
        merged_result.append(sub)
    
    return merged_result
