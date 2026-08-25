import json
from pathlib import Path

import pytest

from youtube_transcript import cli, core
from youtube_transcript.manifest import MANIFEST, render_skill

from conftest import FakeSnippet, FakeTrack

SKILL_FILE = Path(__file__).parent.parent / "skills" / "yt-transcript" / "SKILL.md"

SNIPPETS = [
    FakeSnippet("<i>first</i>\n line", 0.0, 2.0),
    FakeSnippet("second line", 3725.0, 2.0),
]


def run(argv):
    return cli.main(argv)


def test_text_output_carries_timestamps(tracks, capsys):
    tracks(FakeTrack(snippets=SNIPPETS))
    run(["fetch", "dQw4w9WgXcQ"])
    captured = capsys.readouterr()
    assert captured.out.splitlines() == ["[0:00] <i>first</i> line", "[1:02:05] second line"]
    assert "English (en), manual, 2 snippets" in captured.err


def test_untimestamped_text_keeps_the_original_line_breaks(tracks, capsys):
    tracks(FakeTrack(snippets=SNIPPETS))
    run(["fetch", "dQw4w9WgXcQ", "--no-timestamps"])
    assert capsys.readouterr().out.splitlines() == ["<i>first</i>", " line", "second line"]


def test_clean_without_timestamps_is_one_paragraph(tracks, capsys):
    tracks(FakeTrack(snippets=SNIPPETS))
    run(["fetch", "dQw4w9WgXcQ", "--clean", "--no-timestamps"])
    assert capsys.readouterr().out.strip() == "first line second line"


def test_json_goes_to_stdout_and_nothing_else_does(tracks, capsys):
    tracks(FakeTrack(snippets=SNIPPETS))
    run(["fetch", "dQw4w9WgXcQ", "--json"])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["kind"] == "manual"
    assert len(payload["snippets"]) == 2
    assert captured.err == ""


def test_output_file_keeps_stdout_clean(tracks, capsys, tmp_path):
    tracks(FakeTrack(snippets=SNIPPETS))
    destination = tmp_path / "transcript.txt"
    run(["fetch", "dQw4w9WgXcQ", "-o", str(destination)])
    assert capsys.readouterr().out == ""
    assert destination.read_text().startswith("[0:00]")


def test_languages_renders_a_table(tracks, capsys):
    from conftest import FakeLanguage

    tracks(FakeTrack(language_code="en", translation_languages=[FakeLanguage("es")]))
    run(["languages", "dQw4w9WgXcQ"])
    out = capsys.readouterr().out
    assert "CODE" in out and "en" in out and "yes" in out
    assert "1 translation targets available" in out


def test_failure_leaves_stdout_empty_and_sets_the_exit_code(tracks, capsys):
    tracks(FakeTrack(language_code="en", snippets=SNIPPETS))
    with pytest.raises(SystemExit) as raised:
        cli.main(["fetch", "dQw4w9WgXcQ", "-l", "de"])
    captured = capsys.readouterr()
    assert raised.value.code == 5
    assert captured.out == ""
    assert "language_unavailable" in captured.err
    assert "yt-transcript languages dQw4w9WgXcQ" in captured.err


def test_json_failures_are_json_on_stderr(tracks, capsys):
    tracks(FakeTrack(language_code="en", snippets=SNIPPETS))
    with pytest.raises(SystemExit):
        cli.main(["fetch", "dQw4w9WgXcQ", "-l", "de", "--json"])
    captured = capsys.readouterr()
    assert captured.out == ""
    assert json.loads(captured.err)["error"] == "language_unavailable"


def test_describe_emits_the_manifest(capsys):
    run(["describe"])
    assert json.loads(capsys.readouterr().out) == MANIFEST


def test_describe_skill_emits_markdown(capsys):
    run(["describe", "--skill"])
    assert capsys.readouterr().out.strip() == render_skill().strip()


def test_the_skill_carries_frontmatter_every_agent_can_read():
    lines = render_skill().splitlines()
    assert lines[0] == "---"
    closing = lines.index("---", 1)
    frontmatter = dict(line.split(": ", 1) for line in lines[1:closing])
    assert frontmatter["name"] == "yt-transcript"
    assert frontmatter["description"] == MANIFEST["skill"]["description"]


def test_the_packaged_skill_is_in_sync():
    """If this fails, run scripts/package-skill.sh and commit the result."""
    packaged = SKILL_FILE.read_text(encoding="utf-8")
    assert packaged.strip() == render_skill().strip()


def _manifest_flags(command_name):
    command = next(c for c in MANIFEST["commands"] if c["name"] == command_name)
    return {flag for argument in command["arguments"] for flag in argument["flags"]}


def _parser_flags(command_name):
    subparsers = next(
        action for action in cli.build_parser()._actions if hasattr(action, "choices") and action.choices
    )
    parser = subparsers.choices[command_name]
    flags = set()
    for action in parser._actions:
        if action.dest == "help":
            continue
        flags.update(action.option_strings or [action.dest])
    return flags


@pytest.mark.parametrize("command", [c["name"] for c in MANIFEST["commands"]])
def test_the_manifest_matches_the_real_command_surface(command):
    """If this fails, someone added a flag to one side and not the other."""
    assert _manifest_flags(command) == _parser_flags(command)


def test_the_manifest_covers_every_command():
    subparsers = next(
        action for action in cli.build_parser()._actions if hasattr(action, "choices") and action.choices
    )
    assert set(subparsers.choices) == {c["name"] for c in MANIFEST["commands"]}
