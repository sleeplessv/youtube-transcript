#!/usr/bin/env python3
"""Lightweight YouTube transcript fetcher."""

import argparse
import re
import sys
from typing import Optional

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    NoTranscriptFound,
    TranscriptsDisabled,
    VideoUnavailable,
)

# Initialize the API client
api = YouTubeTranscriptApi()


def extract_video_id(url_or_id: str) -> Optional[str]:
    """Extract video ID from a YouTube URL or return the ID if already provided."""
    # Pattern for various YouTube URL formats
    patterns = [
        r"(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})",
        r"^([a-zA-Z0-9_-]{11})$",  # Raw video ID
    ]

    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)

    return None


def clean_text(text: str) -> str:
    """Remove HTML tags and normalize whitespace."""
    # Remove HTML tags
    text = re.sub(r"<[^>]+>", "", text)
    # Replace newlines and multiple spaces with single space
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def format_timestamp(seconds: float) -> str:
    """Format seconds into [MM:SS] or [H:MM:SS] format."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    if hours > 0:
        return f"[{hours}:{minutes:02d}:{secs:02d}]"
    return f"[{minutes}:{secs:02d}]"


def get_transcript(video_id: str, language: str = "en"):
    """Fetch transcript for a YouTube video."""
    try:
        return api.fetch(video_id, languages=[language])
    except NoTranscriptFound:
        # Try to get any available transcript
        transcript_list = api.list(video_id)
        # Try auto-generated first, then manual
        try:
            transcript = transcript_list.find_generated_transcript([language, "en"])
            return transcript.fetch()
        except NoTranscriptFound:
            transcript = transcript_list.find_transcript([language, "en"])
            return transcript.fetch()


def format_transcript(transcript, include_timestamps: bool = True, clean: bool = False) -> str:
    """Format transcript entries into readable text."""
    lines = []
    for entry in transcript:
        text = entry.text.strip()
        if clean:
            text = clean_text(text)
        if include_timestamps:
            timestamp = format_timestamp(entry.start)
            lines.append(f"{timestamp} {text}")
        else:
            lines.append(text)

    if clean and not include_timestamps:
        # Join as continuous text when clean mode without timestamps
        return " ".join(lines)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Fetch transcript from a YouTube video.",
        epilog="Example: python main.py 'https://www.youtube.com/watch?v=VIDEO_ID'",
    )
    parser.add_argument(
        "url",
        help="YouTube video URL or video ID",
    )
    parser.add_argument(
        "-o", "--output",
        help="Save transcript to a file instead of printing to console",
        metavar="FILE",
    )
    parser.add_argument(
        "-l", "--language",
        default="en",
        help="Language code for transcript (default: en)",
    )
    parser.add_argument(
        "--no-timestamps",
        action="store_true",
        help="Exclude timestamps from output",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Remove HTML tags and newlines, output as clean text",
    )

    args = parser.parse_args()

    # Extract video ID
    video_id = extract_video_id(args.url)
    if not video_id:
        print(f"Error: Could not extract video ID from '{args.url}'", file=sys.stderr)
        sys.exit(1)

    print(f"Fetching transcript for video: {video_id}", file=sys.stderr)

    try:
        transcript = get_transcript(video_id, args.language)
        formatted = format_transcript(
            transcript,
            include_timestamps=not args.no_timestamps,
            clean=args.clean,
        )

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(formatted)
            print(f"Transcript saved to: {args.output}", file=sys.stderr)
        else:
            print(formatted)

    except TranscriptsDisabled:
        print("Error: Transcripts are disabled for this video.", file=sys.stderr)
        sys.exit(1)
    except VideoUnavailable:
        print("Error: Video is unavailable or private.", file=sys.stderr)
        sys.exit(1)
    except NoTranscriptFound:
        print("Error: No transcript found for this video.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
