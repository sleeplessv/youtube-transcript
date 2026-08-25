# YouTube Transcript

A command-line tool for fetching YouTube video transcripts, designed so that autonomous
agents can discover its capabilities and construct correct invocations without a human
explaining them first.

## Language

**Video ID**:
The eleven-character identifier YouTube assigns to a video. Accepted directly, or extracted
from a URL.
_Avoid_: Video URL (a URL *contains* a Video ID; the two are not interchangeable)

**Track**:
One caption offering on a video: a single language paired with a single Kind. A video has
zero or more Tracks.
_Avoid_: Caption, subtitle, transcript (a Track is what is *available*, not what was fetched)

**Kind**:
How a Track came to exist. Exactly one of `manual` (a human wrote it), `generated`
(YouTube's speech recognition produced it), or `translated` (YouTube machine-translated
another Track on request).
_Avoid_: Type, source, auto

**Transcript**:
The text fetched from one Track, together with the Track's language and Kind. A Transcript
always states which Track actually produced it.
_Avoid_: Captions, subtitles

**Snippet**:
One timed fragment of a Transcript: its text, its start time, and how long it stays on
screen. Snippets may overlap, and a Snippet's duration is screen time, not speech duration.
_Avoid_: Segment, chunk, line, cue

**Translation Target**:
A language a translatable Track can be machine-translated into. Offered by YouTube per
Track; not every Track is translatable.

**Manifest**:
The tool's machine-readable self-description: every command, its arguments, its output
shape, and worked examples. The single source of truth for the command surface.
_Avoid_: Schema, spec, API description
