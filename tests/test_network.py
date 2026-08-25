"""One live check that YouTube and the library still agree with us.

Deselected by default. Run it with `uv run pytest -m network`, and expect it to fail
from datacenter IPs, which YouTube blocks.
"""

import pytest

from youtube_transcript import core

VIDEO_ID = "dQw4w9WgXcQ"


@pytest.mark.network
def test_a_real_video_still_produces_a_transcript():
    envelope = core.fetch(VIDEO_ID)
    assert envelope["video_id"] == VIDEO_ID
    assert envelope["language_code"] == "en"
    assert envelope["kind"] in {"manual", "generated"}
    assert envelope["snippet_count"] > 0
    assert envelope["text"]


@pytest.mark.network
def test_a_real_video_lists_its_tracks():
    payload = core.languages(VIDEO_ID)
    assert any(track["language_code"] == "en" for track in payload["tracks"])
