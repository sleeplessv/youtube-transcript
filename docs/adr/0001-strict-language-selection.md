# Strict language selection

A request for a language returns that language or fails; it never silently substitutes a
different one. The previous behaviour fell back from the requested language to any
generated track and then to English, so asking for Spanish could return English while
looking like success. For an autonomous consumer that is the worst failure mode available:
undetectable. Fetching now fails with `language_unavailable` and names `yt-transcript
languages <id>` as the next command, and every successful Transcript reports the language
and Kind it actually came from.

## Consequences

Callers that previously got *something* for an unavailable language now get an error and
must handle it. This is deliberate: an explicit error an agent can act on is worth more
than a plausible wrong answer.
