"""
Utilities for parsing and sanitizing SRT subtitle content

The LLM `fix_srt` step rewrites the whole SRT, so it can occasionally corrupt a
timestamp
"""

import re

_TIME_RE = re.compile(
    r"(\d{1,2}):(\d{2}):(\d{2})[,.](\d{1,3})\s*-->\s*"
    r"(\d{1,2}):(\d{2}):(\d{2})[,.](\d{1,3})"
)


def _to_seconds(h: str, m: str, s: str, ms: str) -> float:
    """
    Converts the parts of an SRT timestamp to seconds

    Args:
        h (str): Hours
        m (str): Minutes
        s (str): Seconds
        ms (str): Milliseconds

    Returns:
        The timestamp in seconds
    """
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000


def _fmt(t: float) -> str:
    """
    Formats seconds as an SRT timestamp (`HH:MM:SS,mmm`)

    Args:
        t (float): The time in seconds (clamped to non-negative)

    Returns:
        The formatted SRT timestamp
    """
    total_ms = max(0, round(t * 1000))
    hours, total_ms = divmod(total_ms, 3_600_000)
    minutes, total_ms = divmod(total_ms, 60_000)
    seconds, millis = divmod(total_ms, 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"


def sanitize_srt(srt: str) -> str:
    """
    Repairs invalid SRT timestamps

    Accepts both `,` and `.` millisecond separators

    info: Repairs Applied
        - A cue whose end is at or before its start is given a zero-length
          duration rather than a negative one

        - A cue whose end runs past the next cue's start is clamped to that
          start (this fixes corrupted timestamps that would otherwise span the
          gaps between later cues)

        - Blocks without a parseable `-->` timing line are dropped

        - Cues are renumbered from 1

    Args:
        srt (str): The (possibly malformed) SRT content

    Returns:
        The sanitized SRT content. If nothing parses, the input is returned
        unchanged
    """
    blocks = re.split(r"\n\s*\n", srt.strip())
    cues: list[tuple[float, float, str]] = []

    for block in blocks:
        match = _TIME_RE.search(block)
        if match is None:
            continue
        start = _to_seconds(
            match.group(1), match.group(2), match.group(3), match.group(4)
        )
        end = _to_seconds(
            match.group(5), match.group(6), match.group(7), match.group(8)
        )
        # The text is everything after the timing line.
        text_lines: list[str] = []
        seen_time = False
        for line in block.splitlines():
            if not seen_time:
                if _TIME_RE.search(line):
                    seen_time = True
                continue
            text_lines.append(line)
        cues.append((start, end, "\n".join(text_lines).strip()))

    if not cues:
        return srt

    for i, (start, end, text) in enumerate(cues):
        if end <= start:
            end = start
        if i + 1 < len(cues) and end > cues[i + 1][0]:
            end = cues[i + 1][0]
        cues[i] = (start, end, text)

    out = [
        f"{idx}\n{_fmt(start)} --> {_fmt(end)}\n{text}"
        for idx, (start, end, text) in enumerate(cues, start=1)
    ]
    return "\n\n".join(out) + "\n"
