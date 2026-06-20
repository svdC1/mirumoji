"""
Defines helpers for parsing Docker Compose's plain-progress output stdout lines

question: Why
    - When `docker compose pull` / `up` runs with its output piped, it emits
      one line per progress update
      (e.g. `abc123 Downloading [===>   ] 2MB/50MB`) instead of updating layer
      rows in place

    - Rendering those lines into rich's `Table` or flet's `ListView` grows
      these objects out of bounds and makes output unreadable

info: How It Works
    This module classifies each output line piped from a Docker Compose
    command so that a front-end can collapse them by layer id and colour
    them by status, approaching Docker's native console display

info: No Presentation Here
    - This module only classifies lines

    - Each front-end maps the returned `kind` to its own palette and renders
      the collapsed layers however it likes
"""

import re
from typing import Literal

LineKind = Literal["done", "active", "idle", "free"]
"""
The category of a streamed line

A Docker layer that is `done` / `active` / `idle`, or any other `free` line
"""

# A piped Docker progress line is `<id> <status...>`, where `<id>` is a service
# name or a layer hash and the status is one of Docker's plain-output verbs.
# Compose indents each line with a leading space in non-TTY mode, so the id is
# matched after optional leading whitespace
_DOCKER_PROGRESS = re.compile(
    r"^\s*(?P<id>\S+)\s+(?P<status>Pulling fs layer|Pulling|Pulled|Waiting|"
    r"Downloading|Verifying Checksum|Download complete|Extracting|"
    r"Pull complete|Already exists)\b"
)

_DONE = {
    "Pull complete",
    "Pulled",
    "Already exists",
    "Download complete",
}

_ACTIVE = {
    "Downloading",
    "Extracting",
    "Verifying Checksum",
}


def classify(line: str) -> tuple[LineKind, str | None]:
    """
    Classifies a streamed output line for collapsing and colouring

    Args:
        line (str): A single line of streamed subprocess output

    Returns:
        A `(kind, layer_id)` pair. For a Docker progress line, `kind` is `done`
        / `active` / `idle` and `layer_id` is the layer or service id to
        collapse it under. For any other line, `(free, None)`
    """
    match = _DOCKER_PROGRESS.match(line)
    if match is None:
        return "free", None
    status = match.group("status")
    if status in _DONE:
        return "done", match.group("id")
    if status in _ACTIVE:
        return "active", match.group("id")
    return "idle", match.group("id")
