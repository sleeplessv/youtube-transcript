"""The error taxonomy. Every failure an agent can hit has a code, an exit status
and, where one exists, the next command to run."""

from youtube_transcript_api import _errors as yt

EXIT_CODES = {
    "invalid_input": 2,
    "video_unavailable": 3,
    "transcripts_disabled": 4,
    "language_unavailable": 5,
    "not_translatable": 6,
    "blocked": 7,
    "unknown": 1,
}


class ToolError(Exception):
    def __init__(self, code, message, hint=None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.hint = hint

    @property
    def exit_code(self):
        return EXIT_CODES[self.code]

    def to_dict(self):
        payload = {"error": self.code, "message": self.message}
        if self.hint:
            payload["hint"] = self.hint
        return payload


# Order matters: subclasses before their parents.
_LIBRARY_ERRORS = [
    (yt.InvalidVideoId, "invalid_input"),
    (yt.IpBlocked, "blocked"),
    (yt.RequestBlocked, "blocked"),
    (yt.PoTokenRequired, "blocked"),
    (yt.TranscriptsDisabled, "transcripts_disabled"),
    (yt.AgeRestricted, "video_unavailable"),
    (yt.VideoUnplayable, "video_unavailable"),
    (yt.VideoUnavailable, "video_unavailable"),
    (yt.TranslationLanguageNotAvailable, "not_translatable"),
    (yt.NotTranslatable, "not_translatable"),
    (yt.NoTranscriptFound, "language_unavailable"),
]

_HINTS = {
    "blocked": "YouTube is blocking this IP. Retry through a residential connection, or pass --proxy URL.",
    "language_unavailable": "Run `yt-transcript languages {video_id}` to see which tracks exist.",
    "not_translatable": "Run `yt-transcript languages {video_id}` to see which tracks are translatable and into what.",
}


def translate_library_error(exc, video_id):
    """Turn a youtube-transcript-api exception into a ToolError."""
    for library_error, code in _LIBRARY_ERRORS:
        if isinstance(exc, library_error):
            break
    else:
        code = "unknown"
    hint = _HINTS.get(code)
    # The library appends a multi-paragraph explanation and a GitHub referral.
    # Keep the first sentence; our own hint says what to do next.
    message = next((line for line in str(exc).splitlines() if line.strip()), str(exc))
    message = message.split("This is most likely caused by")[0]
    return ToolError(
        code,
        message.strip(),
        hint.format(video_id=video_id) if hint else None,
    )
