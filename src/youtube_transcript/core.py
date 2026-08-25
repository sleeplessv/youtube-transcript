"""Fetching and shaping transcripts. Everything here returns plain dicts so the CLI
can render them as text or dump them as JSON without a second code path."""

import re

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import YouTubeTranscriptApiException
from youtube_transcript_api.proxies import GenericProxyConfig

from .errors import ToolError, translate_library_error

_URL_PATTERNS = [
    r"(?:youtube\.com/(?:watch\?(?:.*&)?v=|embed/|shorts/|live/)|youtu\.be/)([a-zA-Z0-9_-]{11})",
    r"^([a-zA-Z0-9_-]{11})$",
]


def extract_video_id(url_or_id):
    """Pull the eleven-character video ID out of a URL, or pass one straight through."""
    for pattern in _URL_PATTERNS:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)
    raise ToolError(
        "invalid_input",
        f"Could not find a YouTube video ID in {url_or_id!r}.",
        "Pass a watch/youtu.be/shorts URL, or the 11-character video ID on its own.",
    )


def _api(proxy=None):
    config = GenericProxyConfig(http_url=proxy, https_url=proxy) if proxy else None
    return YouTubeTranscriptApi(proxy_config=config)


def _track_list(video_id, proxy):
    try:
        return _api(proxy).list(video_id)
    except YouTubeTranscriptApiException as exc:
        raise translate_library_error(exc, video_id) from exc


def _fetch(track, video_id):
    try:
        return track.fetch()
    except YouTubeTranscriptApiException as exc:
        raise translate_library_error(exc, video_id) from exc


def _envelope(fetched, kind):
    snippets = [
        {"text": s.text, "start": round(s.start, 3), "duration": round(s.duration, 3)}
        for s in fetched.snippets
    ]
    end = max((s["start"] + s["duration"] for s in snippets), default=0.0)
    return {
        "video_id": fetched.video_id,
        "language": fetched.language,
        "language_code": fetched.language_code,
        "kind": kind,
        "snippet_count": len(snippets),
        "duration_seconds": round(end, 3),
        "text": " ".join(" ".join(s["text"].split()) for s in snippets),
        "snippets": snippets,
    }


def fetch(video_id, language="en", proxy=None):
    """Fetch the transcript in exactly `language`. No silent substitution: see ADR-0001."""
    tracks = _track_list(video_id, proxy)
    try:
        track = tracks.find_transcript([language])
    except YouTubeTranscriptApiException as exc:
        available = ", ".join(t.language_code for t in tracks) or "none"
        raise ToolError(
            "language_unavailable",
            f"No {language!r} track on video {video_id}. Available: {available}.",
            f"Run `yt-transcript languages {video_id}` for the full list, or "
            f"`yt-transcript translate {video_id} --to {language}` to machine-translate one.",
        ) from exc
    kind = "generated" if track.is_generated else "manual"
    return _envelope(_fetch(track, video_id), kind)


def translate(video_id, target, source="en", proxy=None):
    """Machine-translate a track into `target`."""
    tracks = _track_list(video_id, proxy)
    try:
        track = tracks.find_transcript([source])
    except YouTubeTranscriptApiException as exc:
        raise ToolError(
            "language_unavailable",
            f"No {source!r} track to translate from on video {video_id}.",
            f"Run `yt-transcript languages {video_id}` to see which tracks exist.",
        ) from exc
    if not track.is_translatable:
        raise ToolError(
            "not_translatable",
            f"The {source!r} track on video {video_id} cannot be translated.",
            f"Run `yt-transcript languages {video_id}` to see which tracks are translatable.",
        )
    try:
        translated = track.translate(target)
    except YouTubeTranscriptApiException as exc:
        raise ToolError(
            "not_translatable",
            f"YouTube will not translate the {source!r} track into {target!r}.",
            f"Run `yt-transcript languages {video_id} --json` for the translation_targets list.",
        ) from exc
    return _envelope(_fetch(translated, video_id), "translated")


def languages(video_id, proxy=None):
    """List every track on the video, and what they can be translated into."""
    tracks = _track_list(video_id, proxy)
    listed = [
        {
            "language_code": t.language_code,
            "language": t.language,
            "kind": "generated" if t.is_generated else "manual",
            "translatable": t.is_translatable,
        }
        for t in tracks
    ]
    targets = sorted({lang.language_code for t in tracks for lang in t.translation_languages})
    return {"video_id": video_id, "tracks": listed, "translation_targets": targets}
