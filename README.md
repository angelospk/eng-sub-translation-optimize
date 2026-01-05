# Subtitle Optimizer

A Python tool for optimizing subtitle files by reducing CPS (Characters Per Second) and preparing them for translation.

## Features

- **Interjection Removal**: Automatically removes filler words (uh, um, hmm, etc.)
- **Line Reduction**: Reduces 3+ line entries to maximum 2 lines
- **CPS Optimization**: Extends timing and merges subtitles to reduce reading speed
- **LLM Shortening**: Uses Gemini API to intelligently shorten high-CPS segments
- **Translation Prep**: Simplifies subtitles for easier translation

## Installation

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Basic Usage

```bash
# Simple optimization
python subtitle_optimizer.py input.srt -o output.srt

# With verbose output
python subtitle_optimizer.py input.srt -o output.srt -v
```

### Export High-CPS Segments for Manual LLM

```bash
# Export segments that need LLM shortening
python subtitle_optimizer.py input.srt -j high_cps.json

# After manually processing with LLM, apply the results
python subtitle_optimizer.py optimized_input.srt --apply-json high_cps.json
```

### Automatic LLM Shortening

```bash
# Use Gemini API for automatic shortening
export GEMINI_API_KEY="your-api-key"
python subtitle_optimizer.py input.srt --api-key $GEMINI_API_KEY
```

### Custom Parameters

```bash
python subtitle_optimizer.py input.srt \
  --max-cps 18 \           # Target CPS (default: 21)
  --max-chars 80 \         # Max characters per subtitle (default: 90)
  --max-lines 2 \          # Max lines per subtitle (default: 2)
  --max-duration 6 \       # Max duration in seconds (default: 7)
  -v                       # Verbose output
```

## Pipeline Phases

1. **Phase 1**: Interjection Removal - Removes filler words using SubtitleEdit's word list
2. **Phase 1.5**: Line Reduction - Combines lines to meet 2-line maximum
3. **Phase 2**: CPS Optimization - Extends timing and merges adjacent subtitles
4. **Phase 3**: High-CPS Detection - Identifies segments needing text shortening
5. **Phase 4**: LLM Shortening - Uses Gemini API to shorten remaining high-CPS segments

## Professional Subtitle Standards

| Parameter | Value | Description |
|-----------|-------|-------------|
| Min Duration | 0.83s | Minimum subtitle display time |
| Max Duration | 7s | Maximum subtitle display time |
| Target CPS | ≤21 | Characters per second for readability |
| Max Characters | 90 | Maximum characters per subtitle |
| Max Lines | 2 | Maximum lines per subtitle |

## Running Tests

```bash
source venv/bin/activate
python -m pytest tests/ -v
```

## Project Structure

```
subtitle_optimizer.py     # Main CLI entry point
src/
├── __init__.py           # Package exports
├── interjection_remover.py   # Filler word removal
├── interjections_en.py       # English interjection list
├── srt_processor.py          # SRT file I/O
├── cps_optimizer.py          # CPS optimization
└── llm_shortener.py          # Gemini API integration
tests/
├── test_interjection_remover.py
├── test_srt_processor.py
├── test_cps_optimizer.py
└── test_subtitle_optimizer.py
```

## License

MIT
