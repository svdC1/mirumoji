"""
Parses `docker compose ps` output for the running mirumoji application

info: Overview
    - `parse_status` &rarr; turns the raw `ps --format json` output (JSON array
      or NDJSON) into a list of `ServiceStatus`

    - It does not run Docker (the raw output comes from `lifecycle.ps`) and
      does not render anything. Presentation is the caller's job
"""

import json
from typing import Any

from .models import ServiceStatus


def _ports(entry: dict[str, Any]) -> str:
    """
    Summarises a compose `ps` entry's published ports as `host->container`

    Args:
        entry (dict[str, Any]): A single compose `ps` service entry

    Returns:
        A comma-separated published-ports summary, empty when none are
        published
    """
    published = entry.get("Publishers") or []
    seen: list[str] = []
    for pub in published:
        host = pub.get("PublishedPort")
        if not host:
            continue
        mapping = f"{host}->{pub.get('TargetPort')}"
        if mapping not in seen:
            seen.append(mapping)
    return ", ".join(seen)


def parse_status(output: str) -> list[ServiceStatus]:
    """
    Parses `docker compose ps --format json`, tolerating array or NDJSON forms

    Different Docker Compose versions emit either a single JSON array or one
    JSON object per line, so both are handled

    Args:
        output (str): The raw compose `ps --format json` output

    Returns:
        One `ServiceStatus` per service, empty when nothing is running
    """
    text = output.strip()
    if not text:
        return []
    try:
        data = json.loads(text)
        entries = data if isinstance(data, list) else [data]
    except json.JSONDecodeError:
        entries = [
            json.loads(line)
            for line in (raw.strip() for raw in text.splitlines())
            if line
        ]
    return [
        ServiceStatus(
            service=entry.get("Service") or entry.get("Name", ""),
            state=entry.get("State", ""),
            status=entry.get("Status", ""),
            ports=_ports(entry),
        )
        for entry in entries
    ]
