# YouTube Transcript Fetcher

A lightweight Python CLI tool to fetch transcripts from YouTube videos.

## Installation

```bash
uv sync
```

## Usage

```bash
# Fetch transcript from URL
uv run python main.py "https://www.youtube.com/watch?v=VIDEO_ID"

# Or use video ID directly
uv run python main.py VIDEO_ID
```

### Options

| Option | Description |
|--------|-------------|
| `-o FILE`, `--output FILE` | Save transcript to a file |
| `-l CODE`, `--language CODE` | Language code (default: `en`) |
| `--no-timestamps` | Exclude timestamps from output |
| `--clean` | Remove HTML tags and newlines |

### Examples

```bash
# Save to file
uv run python main.py VIDEO_ID -o transcript.txt

# Get Spanish transcript
uv run python main.py VIDEO_ID -l es

# Clean text output (no tags, no newlines, no timestamps)
uv run python main.py VIDEO_ID --clean --no-timestamps
```

## Requirements

- Python 3.13+
- youtube-transcript-api
