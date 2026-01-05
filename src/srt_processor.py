"""SRT file processing module.

Handles reading, writing, and analysis of SRT subtitle files.
"""

import os
import re
from dataclasses import dataclass
from datetime import timedelta
from typing import NamedTuple

import pysrt


@dataclass
class SubtitleEntry:
    """Represents a single subtitle entry."""
    index: int
    start: timedelta
    end: timedelta
    text: str
    
    @property
    def duration(self) -> float:
        """Duration in seconds."""
        return (self.end - self.start).total_seconds()
    
    @property
    def char_count(self) -> int:
        """Character count excluding newlines."""
        return len(self.text.replace('\n', '').replace('\r', ''))
    
    @property
    def line_count(self) -> int:
        """Number of lines in the text."""
        return len(self.text.split('\n'))


class SubtitleStats(NamedTuple):
    """Statistics about subtitle CPS."""
    min_cps: float
    max_cps: float
    avg_cps: float
    high_cps_count: int
    total_count: int


def _pysrt_time_to_timedelta(time) -> timedelta:
    """Convert pysrt time to timedelta."""
    return timedelta(
        hours=time.hours,
        minutes=time.minutes,
        seconds=time.seconds,
        milliseconds=time.milliseconds
    )


def _timedelta_to_pysrt_time(td: timedelta):
    """Convert timedelta to pysrt SubRipTime."""
    total_seconds = td.total_seconds()
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = int(total_seconds % 60)
    milliseconds = int((total_seconds % 1) * 1000)
    return pysrt.SubRipTime(hours, minutes, seconds, milliseconds)


def load_srt(path: str) -> list[SubtitleEntry]:
    """Load SRT file and return list of SubtitleEntry.
    
    Args:
        path: Path to the SRT file.
        
    Returns:
        List of SubtitleEntry objects.
    """
    # Try multiple encodings
    encodings = ['utf-8-sig', 'utf-8', 'latin-1', 'cp1252']
    subs = None
    
    for encoding in encodings:
        try:
            subs = pysrt.open(path, encoding=encoding)
            break
        except (UnicodeDecodeError, UnicodeError):
            continue
    
    if subs is None:
        raise ValueError(f"Could not decode SRT file: {path}")
    
    entries = []
    for sub in subs:
        entry = SubtitleEntry(
            index=sub.index,
            start=_pysrt_time_to_timedelta(sub.start),
            end=_pysrt_time_to_timedelta(sub.end),
            text=sub.text
        )
        entries.append(entry)
    
    return entries


def save_srt(subtitles: list[SubtitleEntry], path: str) -> None:
    """Save subtitle entries to SRT file.
    
    Args:
        subtitles: List of SubtitleEntry objects.
        path: Output file path.
    """
    srt_file = pysrt.SubRipFile()
    
    for i, sub in enumerate(subtitles, 1):
        item = pysrt.SubRipItem(
            index=i,
            start=_timedelta_to_pysrt_time(sub.start),
            end=_timedelta_to_pysrt_time(sub.end),
            text=sub.text
        )
        srt_file.append(item)
    
    srt_file.save(path, encoding='utf-8')


def calculate_cps(subtitle: SubtitleEntry) -> float:
    """Calculate Characters Per Second for a subtitle.
    
    Args:
        subtitle: The subtitle entry.
        
    Returns:
        CPS value. Returns infinity for zero duration.
    """
    duration = subtitle.duration
    if duration <= 0:
        return float('inf')
    
    char_count = subtitle.char_count
    return char_count / duration


def get_subtitle_stats(
    subtitles: list[SubtitleEntry],
    target_cps: float = 21.0
) -> dict:
    """Get CPS statistics for subtitle list.
    
    Args:
        subtitles: List of subtitle entries.
        target_cps: Target CPS threshold.
        
    Returns:
        Dictionary with min_cps, max_cps, avg_cps, high_cps_count, total_count.
    """
    if not subtitles:
        return {
            'min_cps': 0,
            'max_cps': 0,
            'avg_cps': 0,
            'high_cps_count': 0,
            'total_count': 0,
        }
    
    cps_values = [calculate_cps(sub) for sub in subtitles]
    # Filter out infinity for stats
    finite_cps = [c for c in cps_values if c != float('inf')]
    
    if not finite_cps:
        finite_cps = [0]
    
    high_count = sum(1 for c in cps_values if c > target_cps and c != float('inf'))
    
    return {
        'min_cps': min(finite_cps),
        'max_cps': max(finite_cps),
        'avg_cps': sum(finite_cps) / len(finite_cps),
        'high_cps_count': high_count,
        'total_count': len(subtitles),
    }
