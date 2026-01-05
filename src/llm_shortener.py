"""LLM-based text shortening module.

Handles Gemini API integration for shortening high-CPS subtitle segments.
"""

import json
import re
import time
from dataclasses import dataclass, field
from typing import Optional

from .srt_processor import SubtitleEntry, calculate_cps


@dataclass
class HighCPSSegment:
    """A subtitle segment that needs LLM shortening."""
    index: int
    original_text: str
    current_cps: float
    target_cps: float
    chars_to_reduce: int
    context_before: str = ""
    context_after: str = ""
    next_is_uppercase: bool = True  # For trailing punctuation rule
    shortened_text: Optional[str] = None


def find_high_cps_segments(
    subtitles: list[SubtitleEntry],
    target_cps: float = 21.0,
    min_reduction: int = 6
) -> list[HighCPSSegment]:
    """Find subtitle segments that need LLM shortening.
    
    Args:
        subtitles: List of subtitle entries.
        target_cps: Target CPS value.
        min_reduction: Minimum characters to reduce to be worth LLM processing.
        
    Returns:
        List of HighCPSSegment objects needing shortening.
    """
    segments = []
    
    for i, sub in enumerate(subtitles):
        cps = calculate_cps(sub)
        
        if cps <= target_cps or cps == float('inf'):
            continue
        
        # Calculate how many chars need to be reduced
        duration = sub.duration
        current_chars = sub.char_count
        target_chars = int(target_cps * duration)
        chars_to_reduce = current_chars - target_chars
        
        if chars_to_reduce < min_reduction:
            continue
        
        # Get context
        context_before = subtitles[i - 1].text if i > 0 else ""
        context_after = subtitles[i + 1].text if i + 1 < len(subtitles) else ""
        
        # Determine if next text starts with uppercase (for punctuation rule)
        next_is_uppercase = True
        if context_after:
            # Find first letter in context_after
            for char in context_after:
                if char.isalpha():
                    next_is_uppercase = char.isupper()
                    break
        
        segment = HighCPSSegment(
            index=sub.index,
            original_text=sub.text,
            current_cps=cps,
            target_cps=target_cps,
            chars_to_reduce=chars_to_reduce,
            context_before=context_before,
            context_after=context_after,
            next_is_uppercase=next_is_uppercase,
        )
        segments.append(segment)
    
    return segments


def build_shortening_prompt(segments: list[HighCPSSegment]) -> str:
    """Build a prompt for Gemini API to shorten segments.
    
    Args:
        segments: List of segments to shorten.
        
    Returns:
        Prompt string for LLM.
    """
    prompt = """You are a professional subtitle editor. Shorten the following subtitle texts to meet character limits while keeping the meaning intact.

Rules:
1. Keep the core meaning intact
2. Remove unnecessary words (very, really, just, etc.)
3. Use shorter synonyms
4. Keep natural speech flow
5. TRAILING PUNCTUATION RULE: Do NOT end with "." unless next_is_uppercase is true
6. Return ONLY valid JSON array with objects having "index" and "text" keys

Segments to shorten:
"""
    
    for seg in segments:
        char_count = len(seg.original_text.replace('\n', '').replace('\r', ''))
        context_before = seg.context_before[:50] + "..." if seg.context_before else "(start)"
        context_after = seg.context_after[:50] + "..." if seg.context_after else "(end)"
        prompt += f"""
---
Index: {seg.index}
Original ({char_count} chars, need to reduce by {seg.chars_to_reduce}): "{seg.original_text}"
Context before: "{context_before}"
Context after: "{context_after}"
next_is_uppercase: {seg.next_is_uppercase}
---
"""
    
    prompt += """
Return JSON array like: [{"index": 1, "text": "shortened text"}, ...]
"""
    
    return prompt


def shorten_with_llm(
    segments: list[HighCPSSegment],
    api_key: str,
    model: str = "gemini-2.5-flash",
    max_retries: int = 3
) -> list[HighCPSSegment]:
    """Call Gemini API to shorten segments.
    
    Args:
        segments: List of segments to shorten.
        api_key: Gemini API key.
        model: Model name.
        max_retries: Maximum retry attempts.
        
    Returns:
        Segments with shortened_text filled in.
    """
    try:
        from google import genai
    except ImportError:
        raise ImportError("google-genai package required. Install with: pip install google-genai")
    
    client = genai.Client(api_key=api_key)
    prompt = build_shortening_prompt(segments)
    
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt
            )
            
            # Parse JSON response
            text = response.text
            # Extract JSON from response (might be wrapped in markdown)
            json_match = re.search(r'\[.*\]', text, re.DOTALL)
            if json_match:
                results = json.loads(json_match.group())
                
                # Apply results to segments
                result_map = {r['index']: r['text'] for r in results}
                for seg in segments:
                    if seg.index in result_map:
                        seg.shortened_text = result_map[seg.index]
                
                return segments
            
        except Exception as e:
            if 'rate' in str(e).lower() or '429' in str(e):
                # Rate limit - exponential backoff
                wait_time = 2 ** attempt
                time.sleep(wait_time)
            elif attempt == max_retries - 1:
                raise
    
    return segments


def apply_shortened_text(
    subtitles: list[SubtitleEntry],
    segments: list[HighCPSSegment]
) -> list[SubtitleEntry]:
    """Apply shortened text from LLM to subtitles.
    
    Args:
        subtitles: Original subtitle list.
        segments: Segments with shortened_text filled in.
        
    Returns:
        Updated subtitle list.
    """
    # Create a map of index -> shortened text
    shortened_map = {
        seg.index: seg.shortened_text 
        for seg in segments 
        if seg.shortened_text is not None
    }
    
    result = []
    for sub in subtitles:
        if sub.index in shortened_map:
            new_sub = SubtitleEntry(
                index=sub.index,
                start=sub.start,
                end=sub.end,
                text=shortened_map[sub.index]
            )
            result.append(new_sub)
        else:
            result.append(sub)
    
    return result


def export_segments_json(segments: list[HighCPSSegment], path: str) -> None:
    """Export high-CPS segments to JSON for manual LLM processing.
    
    Args:
        segments: List of segments.
        path: Output JSON file path.
    """
    data = []
    for seg in segments:
        data.append({
            'index': seg.index,
            'original_text': seg.original_text,
            'current_cps': round(seg.current_cps, 2),
            'target_cps': seg.target_cps,
            'chars_to_reduce': seg.chars_to_reduce,
            'context_before': seg.context_before[:100] if seg.context_before else "",
            'context_after': seg.context_after[:100] if seg.context_after else "",
            'next_is_uppercase': seg.next_is_uppercase,
            'shortened_text': seg.shortened_text,
        })
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_segments_json(path: str) -> list[HighCPSSegment]:
    """Load segments from JSON file (after manual LLM processing).
    
    Args:
        path: JSON file path.
        
    Returns:
        List of HighCPSSegment objects.
    """
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    segments = []
    for item in data:
        seg = HighCPSSegment(
            index=item['index'],
            original_text=item['original_text'],
            current_cps=item['current_cps'],
            target_cps=item['target_cps'],
            chars_to_reduce=item['chars_to_reduce'],
            context_before=item.get('context_before', ''),
            context_after=item.get('context_after', ''),
            next_is_uppercase=item.get('next_is_uppercase', True),
            shortened_text=item.get('shortened_text'),
        )
        segments.append(seg)
    
    return segments
