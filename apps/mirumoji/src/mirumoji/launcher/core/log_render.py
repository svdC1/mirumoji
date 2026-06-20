"""
Defines helpers for tokenizing container log lines

question: Why
    `docker compose logs` streams plain text prefixed with `<container>  | `
    per line, which breaks the server's styled console log output, making logs
    harder to read

info: How It Works
    - This module splits a `docker compose logs` line into typed `(text, kind)`
      segments so a front-end can colour it like the server's styled console
      handler

info: Token Types
    - Docker Service Prefix
    - Log Level
    - Uuids
    - Paths
    - Urls
    - Numbers
    - Status Keywords

info: No Presentation Here
    - Each front-end maps the returned `kind` to its own palette and builds
      its own spans

    - Levels are returned as the literal level word so the caller can colour
      `INFO` / `WARNING` / `ERROR` distinctly
"""

import re
from typing import Literal

LogKind = Literal[
    "service",
    "level",
    "uuid",
    "url",
    "path",
    "number",
    "ok",
    "bad",
    "warn",
    "plain",
]
"""
All possible types for a log-line segment
"""

# Docker compose prefixes each line with `<container>  | ` when output is piped
_SERVICE = re.compile(r"^(?P<service>\S+)(?P<sep>\s+\|\s)")

# Token Patterns
# Mirrors the server highlighter + a log-level group
# The `_PRIORITY` map breaks ties when two patterns match at the same offset,
# so a structural token (uuid / url / path) wins over a number inside it
_TOKENS: list[tuple[LogKind, re.Pattern[str]]] = [
    (
        "uuid",
        re.compile(
            r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
            r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
        ),
    ),
    ("url", re.compile(r"[a-zA-Z][\w+.-]*://[^\s'\"`]+")),
    ("path", re.compile(r"(?:[A-Za-z]:\\|\\\\|/)[^\s'\"`|]+")),
    ("level", re.compile(r"\b(?:DEBUG|INFO|WARNING|ERROR|CRITICAL)\b")),
    (
        "number",
        re.compile(
            r"(?<![\w.])-?\d+(?:\.\d+)?(?:\s?(?:[KMGT]i?B|ms|s|m|h|fps|%|x))?"
            r"\b"
        ),
    ),
    (
        "ok",
        re.compile(
            r"\b(?i:succeeded|success|started|ready|complete[d]?|saved)\b",
        ),
    ),
    ("bad", re.compile(r"\b(?i:failed|failure|error|aborted|cancell?ed)\b")),
    ("warn", re.compile(r"\b(?i:retry|retrying|fallback|skipped|missing)\b")),
]

_PRIORITY: dict[LogKind, int] = {
    "uuid": 0,
    "url": 1,
    "path": 2,
    "level": 3,
    "ok": 4,
    "bad": 4,
    "warn": 4,
    "number": 5,
}


def tokenize(
    line: str, *, with_service: bool = True
) -> list[tuple[str, LogKind]]:
    """
    Splits a container log line into typed segments for themed rendering

    Args:
        line (str): A single log line, possibly prefixed by `docker compose`
            with `<container>  | `
        with_service (bool): When `True`, the `<container>  | ` prefix is
            emitted as a `service` segment so the front-end can highlight it.
            Pass `False` when logs are filtered to one service and the prefix
            is redundant

    Returns:
        A list of `(text, kind)` segments covering the whole line in order
    """
    segments: list[tuple[str, LogKind]] = []

    body_start = 0
    if with_service:
        prefix = _SERVICE.match(line)
        if prefix is not None:
            segments.append((prefix.group("service"), "service"))
            segments.append((prefix.group("sep"), "plain"))
            body_start = prefix.end()

    body = line[body_start:]

    # Collect every token match, then walk left to right taking non-overlapping
    # spans, preferring the higher-priority kind when two start together
    matches = sorted(
        (
            (match.start(), match.end(), _PRIORITY[kind], kind)
            for kind, pattern in _TOKENS
            for match in pattern.finditer(body)
        ),
        key=lambda item: (item[0], item[2]),
    )

    cursor = 0
    for start, end, _priority, kind in matches:
        if start < cursor:
            continue
        if start > cursor:
            segments.append((body[cursor:start], "plain"))
        segments.append((body[start:end], kind))
        cursor = end

    if cursor < len(body):
        segments.append((body[cursor:], "plain"))

    return segments
