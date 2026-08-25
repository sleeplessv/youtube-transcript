import pytest
from youtube_transcript_api import _errors as yt

from youtube_transcript import core
from youtube_transcript.errors import ToolError, translate_library_error

from conftest import FakeLanguage, FakeSnippet, FakeTrack


@pytest.mark.parametrize(
    "given",
    [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://www.youtube.com/watch?list=PL123&v=dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ",
        "https://www.youtube.com/shorts/dQw4w9WgXcQ",
        "https://www.youtube.com/embed/dQw4w9WgXcQ",
        "https://www.youtube.com/live/dQw4w9WgXcQ",
        "dQw4w9WgXcQ",
    ],
)
def test_extracts_the_video_id(given):
    assert core.extract_video_id(given) == "dQw4w9WgXcQ"


def test_rejects_anything_that_is_not_a_video_id():
    with pytest.raises(ToolError) as raised:
        core.extract_video_id("https://example.com/not-a-video")
    assert raised.value.code == "invalid_input"
    assert raised.value.exit_code == 2


def test_fetch_reports_the_track_it_actually_used(tracks):
    tracks(FakeTrack(snippets=[FakeSnippet("hello\n there", 0.0, 2.5)], is_generated=True))
    envelope = core.fetch("dQw4w9WgXcQ")
    assert envelope["kind"] == "generated"
    assert envelope["language_code"] == "en"
    assert envelope["text"] == "hello there"
    assert envelope["snippet_count"] == 1
    assert envelope["duration_seconds"] == 2.5


def test_fetch_marks_human_written_tracks_as_manual(tracks):
    tracks(FakeTrack(snippets=[FakeSnippet("hi", 0.0, 1.0)], is_generated=False))
    assert core.fetch("dQw4w9WgXcQ")["kind"] == "manual"


def test_fetch_never_substitutes_another_language(tracks):
    """ADR-0001: asking for German must not quietly return English."""
    tracks(FakeTrack(language_code="en", snippets=[FakeSnippet("hi", 0.0, 1.0)]))
    with pytest.raises(ToolError) as raised:
        core.fetch("dQw4w9WgXcQ", language="de")
    assert raised.value.code == "language_unavailable"
    assert raised.value.exit_code == 5
    assert "en" in raised.value.message
    assert "yt-transcript languages dQw4w9WgXcQ" in raised.value.hint


def test_translate_marks_the_result_as_translated(tracks):
    tracks(
        FakeTrack(
            snippets=[FakeSnippet("hello", 0.0, 1.0)],
            translation_languages=[FakeLanguage("es")],
        )
    )
    envelope = core.translate("dQw4w9WgXcQ", target="es")
    assert envelope["kind"] == "translated"
    assert envelope["language_code"] == "es"


def test_translate_refuses_an_untranslatable_track(tracks):
    tracks(FakeTrack(snippets=[FakeSnippet("hello", 0.0, 1.0)], translation_languages=[]))
    with pytest.raises(ToolError) as raised:
        core.translate("dQw4w9WgXcQ", target="es")
    assert raised.value.code == "not_translatable"
    assert raised.value.exit_code == 6


def test_translate_refuses_a_target_youtube_will_not_produce(tracks):
    tracks(
        FakeTrack(
            snippets=[FakeSnippet("hello", 0.0, 1.0)],
            translation_languages=[FakeLanguage("fr")],
        )
    )
    with pytest.raises(ToolError) as raised:
        core.translate("dQw4w9WgXcQ", target="es")
    assert raised.value.code == "not_translatable"


def test_languages_lists_tracks_and_targets(tracks):
    tracks(
        FakeTrack(language_code="en", translation_languages=[FakeLanguage("es"), FakeLanguage("fr")]),
        FakeTrack(language_code="de", language="German", is_generated=True),
    )
    payload = core.languages("dQw4w9WgXcQ")
    assert payload["translation_targets"] == ["es", "fr"]
    assert payload["tracks"] == [
        {"language_code": "en", "language": "English", "kind": "manual", "translatable": True},
        {"language_code": "de", "language": "German", "kind": "generated", "translatable": False},
    ]


@pytest.mark.parametrize(
    ("exception", "code", "exit_code"),
    [
        (yt.InvalidVideoId("x"), "invalid_input", 2),
        (yt.VideoUnavailable("x"), "video_unavailable", 3),
        (yt.AgeRestricted("x"), "video_unavailable", 3),
        (yt.TranscriptsDisabled("x"), "transcripts_disabled", 4),
        (yt.IpBlocked("x"), "blocked", 7),
        (yt.RequestBlocked("x"), "blocked", 7),
        (yt.PoTokenRequired("x"), "blocked", 7),
        (yt.NotTranslatable("x"), "not_translatable", 6),
        (yt.YouTubeDataUnparsable("x"), "unknown", 1),
    ],
)
def test_library_errors_map_to_the_taxonomy(exception, code, exit_code):
    error = translate_library_error(exception, "dQw4w9WgXcQ")
    assert (error.code, error.exit_code) == (code, exit_code)
    assert error.message


def test_blocked_errors_point_at_the_proxy_flag(tracks):
    tracks(list_error=yt.IpBlocked("dQw4w9WgXcQ"))
    with pytest.raises(ToolError) as raised:
        core.fetch("dQw4w9WgXcQ")
    assert "--proxy" in raised.value.hint
