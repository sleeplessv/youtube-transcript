"""The manifest is the single source of truth for the command surface. `describe`
prints it as JSON, `describe --skill` renders it as agent instructions, and a test
asserts it against the argparse tree so a new flag cannot drift out of it."""

from . import __version__
from .errors import EXIT_CODES

REPO = "https://github.com/sleeplessv/youtube-transcript"

_VIDEO_ARG = {
    "flags": ["video"],
    "description": "YouTube URL (watch, youtu.be, shorts, embed, live) or bare 11-character video ID.",
}
_PROXY_ARG = {
    "flags": ["--proxy"],
    "description": "Route requests through an HTTP/SOCKS proxy. Use this when you hit the `blocked` error.",
}
_JSON_ARG = {
    "flags": ["--json"],
    "description": "Emit JSON on stdout instead of human-readable text.",
}

_TRANSCRIPT_OUTPUT = {
    "video_id": "string",
    "language": "string, the human-readable name of the track that answered",
    "language_code": "string, e.g. 'en'",
    "kind": "one of manual, generated, translated",
    "snippet_count": "integer",
    "duration_seconds": "float, end of the last snippet",
    "text": "string, the whole transcript with whitespace collapsed",
    "snippets": "array of {text, start, duration}; start and duration are seconds",
}

MANIFEST = {
    "tool": "yt-transcript",
    "version": __version__,
    "summary": "Fetch transcripts from YouTube videos.",
    "install": {
        "run_without_installing": f"uvx --from git+{REPO} yt-transcript <command>",
        "install_once": f"uv tool install git+{REPO}",
        "install_from_a_local_clone": "uv tool install --editable .",
    },
    "conventions": [
        "stdout carries the payload and nothing else. Progress and errors go to stderr, so `> file` is always safe.",
        "Text output is the default. Pass --json for a machine-readable envelope.",
        "Language selection is strict: asking for a language you cannot have is an error, never a silent substitution.",
        "Every error names the command that will get you unstuck. Read the hint before guessing.",
    ],
    "commands": [
        {
            "name": "fetch",
            "summary": "Fetch the transcript of one video in one language.",
            "arguments": [
                _VIDEO_ARG,
                {
                    "flags": ["-l", "--language"],
                    "description": "Language code to fetch. Defaults to 'en'. Fails if that exact language has no track.",
                },
                {
                    "flags": ["-o", "--output"],
                    "description": "Write to this file instead of stdout.",
                },
                {
                    "flags": ["--no-timestamps"],
                    "description": "Text output only: drop the [MM:SS] prefixes.",
                },
                {
                    "flags": ["--clean"],
                    "description": "Text output only: strip residual HTML tags and collapse whitespace.",
                },
                _JSON_ARG,
                _PROXY_ARG,
            ],
            "output": _TRANSCRIPT_OUTPUT,
            "examples": [
                "yt-transcript fetch 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'",
                "yt-transcript fetch dQw4w9WgXcQ --json > transcript.json",
                "yt-transcript fetch dQw4w9WgXcQ --clean --no-timestamps",
                "yt-transcript fetch dQw4w9WgXcQ -l de",
            ],
        },
        {
            "name": "languages",
            "summary": "List every track on a video and what it can be translated into. Run this first when fetch reports language_unavailable.",
            "arguments": [_VIDEO_ARG, _JSON_ARG, _PROXY_ARG],
            "output": {
                "video_id": "string",
                "tracks": "array of {language_code, language, kind, translatable}",
                "translation_targets": "array of language codes YouTube will translate into (--json only; text output shows a count)",
            },
            "examples": [
                "yt-transcript languages dQw4w9WgXcQ",
                "yt-transcript languages dQw4w9WgXcQ --json",
            ],
        },
        {
            "name": "translate",
            "summary": "Machine-translate an existing track into another language.",
            "arguments": [
                _VIDEO_ARG,
                {
                    "flags": ["--to"],
                    "description": "Target language code. Required.",
                },
                {
                    "flags": ["--from"],
                    "description": "Source track to translate from. Defaults to 'en'.",
                },
                {
                    "flags": ["-o", "--output"],
                    "description": "Write to this file instead of stdout.",
                },
                {
                    "flags": ["--no-timestamps"],
                    "description": "Text output only: drop the [MM:SS] prefixes.",
                },
                {
                    "flags": ["--clean"],
                    "description": "Text output only: strip residual HTML tags and collapse whitespace.",
                },
                _JSON_ARG,
                _PROXY_ARG,
            ],
            "output": dict(_TRANSCRIPT_OUTPUT, kind="always 'translated'"),
            "examples": [
                "yt-transcript translate dQw4w9WgXcQ --to es",
                "yt-transcript translate dQw4w9WgXcQ --from de --to fr --json",
            ],
        },
        {
            "name": "describe",
            "summary": "Print this manifest as JSON, or agent instructions as Markdown.",
            "arguments": [
                {
                    "flags": ["--skill"],
                    "description": "Print Markdown instructions for an agent instead of JSON.",
                }
            ],
            "output": {"": "This manifest, or Markdown when --skill is passed."},
            "examples": [
                "yt-transcript describe",
                "yt-transcript describe --skill > .claude/skills/yt-transcript/SKILL.md",
            ],
        },
    ],
    "exit_codes": {
        "0": "success",
        str(EXIT_CODES["unknown"]): "unknown: an unrecognised failure. The message is passed through from the underlying library.",
        str(EXIT_CODES["invalid_input"]): "invalid_input: the argument was not a usable URL or video ID.",
        str(EXIT_CODES["video_unavailable"]): "video_unavailable: private, deleted, age-restricted, or otherwise unplayable.",
        str(EXIT_CODES["transcripts_disabled"]): "transcripts_disabled: the uploader turned captions off. Nothing will fix this.",
        str(EXIT_CODES["language_unavailable"]): "language_unavailable: no track in that language. Run `languages` next.",
        str(EXIT_CODES["not_translatable"]): "not_translatable: that track cannot be translated, or not into that target. Run `languages` next.",
        str(EXIT_CODES["blocked"]): "blocked: YouTube is refusing this IP. Retry from a residential connection or pass --proxy.",
    },
}


def render_skill():
    """Render the manifest as Markdown instructions for an agent."""
    m = MANIFEST
    out = [
        f"# {m['tool']}",
        "",
        f"{m['summary']} Version {m['version']}.",
        "",
        "## Running it",
        "",
        "```bash",
        "# no install needed",
        m["install"]["run_without_installing"],
        "",
        "# or install once, then call it directly",
        m["install"]["install_once"],
        "```",
        "",
        "## How it behaves",
        "",
    ]
    out += [f"- {line}" for line in m["conventions"]]
    out += ["", "## Commands", ""]
    for command in m["commands"]:
        out += [f"### `{command['name']}`", "", command["summary"], ""]
        for argument in command["arguments"]:
            out.append(f"- `{', '.join(argument['flags'])}`: {argument['description']}")
        fields = [f"- `{k}`: {v}" for k, v in command["output"].items() if k]
        if fields:
            out += ["", "Output fields:", "", *fields]
        out += ["", "```bash", *command["examples"], "```", ""]
    out += ["## Exit codes", ""]
    out += [f"- `{code}`: {meaning}" for code, meaning in sorted(m["exit_codes"].items())]
    out.append("")
    return "\n".join(out)
