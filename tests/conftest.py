"""Fakes standing in for youtube-transcript-api, so the unit tests never touch the network."""

from dataclasses import dataclass, field

import pytest

from youtube_transcript import core


@dataclass
class FakeSnippet:
    text: str
    start: float
    duration: float


@dataclass
class FakeFetched:
    snippets: list
    video_id: str = "dQw4w9WgXcQ"
    language: str = "English"
    language_code: str = "en"
    is_generated: bool = False


@dataclass
class FakeTrack:
    language_code: str = "en"
    language: str = "English"
    is_generated: bool = False
    translation_languages: list = field(default_factory=list)
    snippets: list = field(default_factory=list)
    fetch_error: Exception = None

    @property
    def is_translatable(self):
        return bool(self.translation_languages)

    def fetch(self):
        if self.fetch_error:
            raise self.fetch_error
        return FakeFetched(
            self.snippets,
            language=self.language,
            language_code=self.language_code,
            is_generated=self.is_generated,
        )

    def translate(self, language_code):
        codes = [lang.language_code for lang in self.translation_languages]
        if language_code not in codes:
            from youtube_transcript_api._errors import TranslationLanguageNotAvailable

            raise TranslationLanguageNotAvailable("dQw4w9WgXcQ")
        return FakeTrack(language_code=language_code, language=language_code.upper(), snippets=self.snippets)


@dataclass
class FakeLanguage:
    language_code: str
    language: str = "Some language"


class FakeTrackList:
    def __init__(self, tracks):
        self._tracks = tracks

    def __iter__(self):
        return iter(self._tracks)

    def find_transcript(self, language_codes):
        for code in language_codes:
            for track in self._tracks:
                if track.language_code == code:
                    return track
        from youtube_transcript_api._errors import NoTranscriptFound

        raise NoTranscriptFound("dQw4w9WgXcQ", language_codes, self)

    def __str__(self):
        return "fake track list"


@pytest.fixture
def tracks(monkeypatch):
    """Install a fake track list. Call the returned function with FakeTracks or an Exception."""

    def install(*tracks, list_error=None):
        class FakeApi:
            def list(self, video_id):
                if list_error:
                    raise list_error
                return FakeTrackList(list(tracks))

        monkeypatch.setattr(core, "_api", lambda proxy=None: FakeApi())

    return install
