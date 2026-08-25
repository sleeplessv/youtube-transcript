# yt-transcript

Fetch transcripts from YouTube videos. The CLI is built so an agent can work out how to
drive it without a human explaining first: `yt-transcript describe` prints a machine-readable
manifest of every command, and every error names the command that gets you unstuck.

## Install

```bash
# run it without installing anything
uvx --from git+https://github.com/sleeplessv/youtube-transcript yt-transcript fetch VIDEO_ID

# or install once and call it directly
uv tool install git+https://github.com/sleeplessv/youtube-transcript
```

Working on the tool itself? `uv tool install --editable .` from a clone, and the installed
command tracks your edits.

## Use

```bash
yt-transcript fetch "https://www.youtube.com/watch?v=VIDEO_ID"
yt-transcript fetch VIDEO_ID --json > transcript.json
yt-transcript fetch VIDEO_ID --clean --no-timestamps
yt-transcript languages VIDEO_ID
yt-transcript translate VIDEO_ID --to es
```

Text output is the default. `--json` gives you an envelope with `language`, `language_code`,
`kind`, `text`, and timed `snippets`.

Two rules worth knowing before you script against it. Stdout carries the payload and nothing
else, so `> file` never picks up a progress line or an error. And language selection is
strict: `-l de` returns German or fails with `language_unavailable`, and it will never hand
you English while looking like it worked. See
[ADR-0001](docs/adr/0001-strict-language-selection.md).

## Agents

```bash
yt-transcript describe             # JSON manifest: commands, arguments, output fields, exit codes
yt-transcript describe --skill     # the same thing as Markdown instructions
```

To drop the instructions into a project as a skill:

```bash
mkdir -p .claude/skills/yt-transcript
yt-transcript describe --skill > .claude/skills/yt-transcript/SKILL.md
```

## Exit codes

| Code | Meaning | What to do |
|------|---------|------------|
| 0 | success | |
| 1 | `unknown` | Read the message; it comes from the underlying library. |
| 2 | `invalid_input` | Pass a YouTube URL or a bare 11-character video ID. |
| 3 | `video_unavailable` | Private, deleted, age-restricted, or unplayable. |
| 4 | `transcripts_disabled` | The uploader turned captions off. Nothing will fix this. |
| 5 | `language_unavailable` | Run `yt-transcript languages VIDEO_ID`. |
| 6 | `not_translatable` | Run `yt-transcript languages VIDEO_ID --json` for the targets. |
| 7 | `blocked` | YouTube is refusing this IP. Use a residential connection or `--proxy URL`. |

## Development

```bash
uv sync
uv run pytest              # unit tests, no network
uv run pytest -m network   # live smoke test against YouTube
```

The manifest in `src/youtube_transcript/manifest.py` is the single source of truth for the
command surface. A test asserts it against the argparse tree, so adding a flag in one place
and not the other fails the suite.

Requires Python 3.10 or newer.
