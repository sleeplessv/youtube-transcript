#!/usr/bin/env bash
# Regenerate skills/yt-transcript/SKILL.md and zip it for Claude Desktop
# (Settings > Capabilities > Skills > Upload skill).
set -euo pipefail

root=$(cd "$(dirname "$0")/.." && pwd)
cd "$root"

uv run yt-transcript describe --skill > skills/yt-transcript/SKILL.md
mkdir -p dist
rm -f dist/yt-transcript-skill.zip
(cd skills && zip -q -r ../dist/yt-transcript-skill.zip yt-transcript)
echo "dist/yt-transcript-skill.zip"
