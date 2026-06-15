# Changelog

All notable changes to this project will be documented in this file

The format is based on [`Keep a Changelog`](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [`Semantic Versioning`](https://semver.org/spec/v2.0.0.html)
starting from **`v3.0.0`**

???+ warning "Pre-`v3.0.0`"
    - `v1.0.0` – `v2.6.0` used semver-like tags but without a formal policy or changelog
    - Their history is preserved in [`GitHub Releases`](https://github.com/svdC1/mirumoji/releases)

---

## [3.0.0] - 2026-06-15

A structural and packaging rewrite of `Mirumoji`

- The backend + CLI are merged into a single, pip-installable `mirumoji` package, and the release, docs, and  dev-container tooling are rebuilt around it

- The core immersion workflow is unchanged from `2.6.0`, the `Launcher` (CLI + Desktop GUI) is substantially expanded, and LLM support is no longer limited to `OpenAI`

- There is intentionally no `2.6.0` &rarr; `3.0.0` diff, since nearly everything moved internally, so this entry   answers `What Carried Over?` + `What's New?` + `How To Run It` instead

### What Carried Over From `2.6.0`

The immersion workflow is `Unchanged`

- Upload local videos, anime episodes, or audio for clickable `tokenized Japanese subtitles` with dictionary lookups

- Transcribe audio / generate subtitles with `Whisper`

- Get word / sentence breakdowns from LLMs, or prompt the LLM to refine the
  Whisper-generated subtitles

- Save `clips` and export them to an `Anki` deck

- Organize your data (clips, LLM templates, files, transcriptions, ...) on the
  server by profile

- Self-host the `Docker Compose Application` with `Local-NVIDIA-GPU` /
  `Modal Cloud-GPU Offload` backend options

- Access the application via HTTPS from any device on your local network using
  the automatically generated self-signed certificate

### What's New / Expanded

#### Multiple LLM Providers *(New)*

`2.6.0` required an `OpenAI` API key

`3.0.0` makes LLM features `completely optional` and adds `Anthropic (Claude)` + `Google (Gemini)` + `Any Custom OpenAI-Compatible Endpoint` support via a provider / model picker

#### CLI Launcher *(Expanded)*

The `2.6.0` CLI had 5 commands (`launch` / `shutdown` / `launch_local` /
`build` / `gui`) driven by interactive prompts and a hand-managed `.env`

`3.0.0` rebuilds it on `Typer` / `Rich`, adds the `status` / `logs` / `doctor`
/ `server` / `render` commands + a managed-config surface (`config set/delete/import/show/path/clear`)

#### Desktop Launcher *(Expanded)*

The `2.6.0` `flaskwebgui` / `PyInstaller` window is rebuilt on `Flet` and gains
a `Settings` panel where you can configure the transcription backend, image
source, and LLM / Modal keys. It also has full environment checks, live status
display, and Docker Compose log filtering

#### Modal Offload *(Hardened)*

`Modal` GPU jobs stream their media through a per-job ephemeral `Modal Volume`
instead of a baked image mount, so long media (multi-hour, multi-GB) transcodes
and transcribes reliably. Large uploads also stream at full speed rather than
being throttled at the reverse proxy

### How To Run It

The [`Setup Section`](setup/index.md) contains detailed information on all of
the ways that you can get `Mirumoji` running

### Upgrading From `2.6.0`

???+ warning "Your Data Does Not Carry Over"
    The database schema changed in `3.0.0`, so existing `2.6.0` profiles,
    clips, transcripts, and templates are `NOT` migrated
    
    Treat `3.0.0` as a fresh install.

??? info "Additional Details &rarr; Changed Surfaces"
    - `Package` &rarr; `apps/backend` + `apps/cli` merged into one
      `apps/mirumoji/` package published to PyPI as `mirumoji`

    - `CI / CD` &rarr; 12 workflows redesigned as an orchestrated `release.yaml`
      calling reusable `_version` / `_images` / `_pypi` / `_pages` / `_desktop`
      workflows. Images are published to `Docker Hub` only (GHCR dropped)

    - `Docs` &rarr; MkDocs Material custom CSS theme, `mkdocstrings-python` (API) + `TypeDoc` (frontend API),   `awesome-nav` structure

    - `Dev Containers` &rarr; fixed builds + `postCreateCommand` bootstrap, and
      `flake8` changed to `ruff`

    `Community` &rarr; community files moved to `.github/`, `YAML` issue forms, quality-gate PR template
---
