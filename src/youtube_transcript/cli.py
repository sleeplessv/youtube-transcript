"""The command-line entry point."""

import argparse
import json
import re
import sys

from . import __version__, core
from .errors import ToolError
from .manifest import MANIFEST, render_skill


def _timestamp(seconds):
    hours, remainder = divmod(int(seconds), 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"[{hours}:{minutes:02d}:{secs:02d}]"
    return f"[{minutes}:{secs:02d}]"


def render_transcript(envelope, timestamps=True, clean=False):
    """Render a transcript envelope as text."""
    lines = []
    for snippet in envelope["snippets"]:
        text = snippet["text"].strip()
        if clean:
            text = re.sub(r"<[^>]+>", "", text)
        if clean or timestamps:
            # A timestamped line has to stay one line, and YouTube wraps its captions.
            text = " ".join(text.split())
        lines.append(f"{_timestamp(snippet['start'])} {text}" if timestamps else text)
    if clean and not timestamps:
        return " ".join(lines)
    return "\n".join(lines)


def render_languages(payload):
    """Render a track listing as a text table."""
    rows = [("CODE", "KIND", "TRANSLATABLE", "LANGUAGE")] + [
        (t["language_code"], t["kind"], "yes" if t["translatable"] else "no", t["language"])
        for t in payload["tracks"]
    ]
    if len(rows) == 1:
        return f"No tracks on video {payload['video_id']}."
    widths = [max(len(row[i]) for row in rows) for i in range(4)]
    lines = ["  ".join(cell.ljust(widths[i]) for i, cell in enumerate(row)).rstrip() for row in rows]
    count = len(payload["translation_targets"])
    if count:
        lines += ["", f"{count} translation targets available. Use --json to list them."]
    return "\n".join(lines)


def _emit(text, output_path):
    if output_path:
        with open(output_path, "w", encoding="utf-8") as handle:
            handle.write(text + "\n")
        print(f"Written to {output_path}", file=sys.stderr)
    else:
        print(text)


def _transcript_command(args, envelope):
    if args.json:
        _emit(json.dumps(envelope, ensure_ascii=False, indent=2), args.output)
        return
    print(
        f"{envelope['language']} ({envelope['language_code']}), {envelope['kind']}, "
        f"{envelope['snippet_count']} snippets",
        file=sys.stderr,
    )
    _emit(
        render_transcript(envelope, timestamps=not args.no_timestamps, clean=args.clean),
        args.output,
    )


def _add_video_argument(parser):
    parser.add_argument("video", help=MANIFEST["commands"][0]["arguments"][0]["description"])


def _add_shared_arguments(parser):
    parser.add_argument("--json", action="store_true", help="Emit JSON on stdout instead of text.")
    parser.add_argument("--proxy", help="Route requests through an HTTP/SOCKS proxy.", metavar="URL")


def _add_transcript_arguments(parser):
    parser.add_argument("-o", "--output", help="Write to this file instead of stdout.", metavar="FILE")
    parser.add_argument("--no-timestamps", action="store_true", help="Text output only: drop [MM:SS] prefixes.")
    parser.add_argument("--clean", action="store_true", help="Text output only: strip HTML tags and collapse whitespace.")
    _add_shared_arguments(parser)


def build_parser():
    parser = argparse.ArgumentParser(
        prog="yt-transcript",
        description=MANIFEST["summary"],
        epilog="Run `yt-transcript describe` for a machine-readable manifest of every command.",
    )
    parser.add_argument("--version", action="version", version=__version__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    fetch = subparsers.add_parser("fetch", help=MANIFEST["commands"][0]["summary"])
    _add_video_argument(fetch)
    fetch.add_argument("-l", "--language", default="en", help="Language code to fetch. Defaults to 'en'.", metavar="CODE")
    _add_transcript_arguments(fetch)

    languages = subparsers.add_parser("languages", help=MANIFEST["commands"][1]["summary"])
    _add_video_argument(languages)
    _add_shared_arguments(languages)

    translate = subparsers.add_parser("translate", help=MANIFEST["commands"][2]["summary"])
    _add_video_argument(translate)
    translate.add_argument("--to", required=True, dest="to", help="Target language code.", metavar="CODE")
    translate.add_argument("--from", default="en", dest="source", help="Source track. Defaults to 'en'.", metavar="CODE")
    _add_transcript_arguments(translate)

    describe = subparsers.add_parser("describe", help=MANIFEST["commands"][3]["summary"])
    describe.add_argument("--skill", action="store_true", help="Print Markdown agent instructions instead of JSON.")

    return parser


def run(args):
    if args.command == "describe":
        print(render_skill() if args.skill else json.dumps(MANIFEST, indent=2))
        return

    video_id = core.extract_video_id(args.video)
    if args.command == "fetch":
        _transcript_command(args, core.fetch(video_id, args.language, args.proxy))
    elif args.command == "translate":
        _transcript_command(args, core.translate(video_id, args.to, args.source, args.proxy))
    else:
        payload = core.languages(video_id, args.proxy)
        text = json.dumps(payload, ensure_ascii=False, indent=2) if args.json else render_languages(payload)
        print(text)


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        run(args)
    except ToolError as error:
        if getattr(args, "json", False):
            print(json.dumps(error.to_dict(), indent=2), file=sys.stderr)
        else:
            print(f"Error [{error.code}]: {error.message}", file=sys.stderr)
            if error.hint:
                print(error.hint, file=sys.stderr)
        sys.exit(error.exit_code)
    except KeyboardInterrupt:
        sys.exit(130)


if __name__ == "__main__":
    main()
