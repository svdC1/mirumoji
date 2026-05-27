# mirumoji

Self-hostable Japanese language immersion tool.

This directory contains the unified Python package for both the **server** (FastAPI backend) and the **CLI/GUI launcher**.

## Quickstart (end users)

```bash
pip install mirumoji
mirumoji launch
```

## Package extras

| Extra | Purpose |
|-------|---------|
| *(base)* | CLI launcher only — minimal deps, no ML |
| `server` | FastAPI server + Whisper + all ML deps (used in Docker image) |
| `gui` | Desktop GUI launcher |
| `dev` | ruff, mypy, pytest, pip-tools |

## Development

```bash
pip install -e ".[server,dev]"
mirumoji-server          # start FastAPI server directly (port 8000)
mirumoji launch --build  # build + launch via Docker Compose
```

See the full documentation at <https://svdc1.github.io/mirumoji/docs>.
