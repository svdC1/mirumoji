# Changelog

All notable changes to this project will be documented in this file

The format is based on [`Keep a Changelog`](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [`Semantic Versioning`](https://semver.org/spec/v2.0.0.html)
starting from **`v3.0.0`**

???+ warning "Pre-`v3.0.0`"
    - `v1.0.0` – `v2.6.0` used semver-like tags but without a formal policy or changelog
    - Their history is preserved in [`GitHub Releases`](https://github.com/svdC1/mirumoji/releases)

???+ danger "`v3.0.0` Is `v0.1.0`"
    - Since `Mirumoji` underwent a complete refactoring / rewriting and has only started following `Semantic Versioning` in `v3.0.0`, it should be treated as a initial release

    - This means that the following `v3.x` versions **MIGHT STILL CONTAIN BREAKING CHANGES**

    - These changes will be clearly documented in this changelog

---

## [`3.1.0`](https://github.com/svdC1/mirumoji/releases/tag/v3.1.0) - 2026-06-20

This release moves every long-running media operation into a background job system,
adds batch processing so one operation can run over many files at once, and makes the
GPU Docker images much smaller. As a `v3.x` release (see the `v0.1.0` note above) it
includes a few breaking changes, listed first

### Breaking Changes

- `REST API` &rarr; the old one-shot endpoints for transcription, subtitle
  generation, conversion, and subtitle cleanup were removed. These operations now run
  through the background job system instead

- `REST API` &rarr; word breakdowns and sentence explanations are now sent as a live
  stream while they are generated, rather than as a single response at the end

- `CLI` &rarr; the `mirumoji server` command moved into a new development-only group
  and is now `mirumoji dev server`

- `Database` &rarr; the database format changed and is not upgraded automatically
  from `3.0.0`. Reset it when upgrading by running `mirumoji down -v` (this clears
  local data, in keeping with the pre-1.0 note above)

### Added

- `Server` &rarr; long operations (transcription, subtitle generation, conversion,
  and LLM subtitle cleanup) now run in the background. A file is uploaded once, and
  any number of operations can then run on it without uploading it again

- `Server` &rarr; batch processing runs one operation across many files at once and
  tracks each file on its own. On the Modal backend the files are processed in
  parallel

- `Frontend` &rarr; a task tray keeps your running and finished jobs visible as you
  move around the app, and loads each result back in when it is done

- `Frontend` &rarr; new `Files` and `Tasks` sections on the dashboard let you upload
  files or a whole folder, select several and run them as a batch, browse the full
  job history, and open each result

- `Frontend` &rarr; when setting up an LLM, you can now pick the model from a
  searchable list of your provider's models instead of typing its exact name

- `CLI` &rarr; `mirumoji dev up` builds and runs the app from a local source
  checkout, for testing the Docker setup during development

### Changed

- `Frontend` &rarr; running an operation in the player no longer freezes the toolbar.
  It is handed to the task tray, which loads the result back in when it finishes. The
  video player was also reworked into a shared component that clip previews reuse

- `Frontend` &rarr; a phone held sideways now uses the mobile layout, since the
  desktop layout only starts at tablet width

- `Launcher` &rarr; the launcher's logs and the Docker download progress are tidier
  and easier to follow, in both the CLI and the desktop app

- `Docker Images` &rarr; the GPU images are roughly 5 GB smaller. PyTorch was removed
  because transcription does not need it, the speech model now downloads on first use
  instead of being shipped inside the image, and the Modal image loads faster

### Fixed

- `Frontend` &rarr; the player now handles video formats your browser cannot play
  (such as `.mkv` on iOS) by offering to convert them to MP4 instead of showing a
  broken player. Loading a different video also resets the saved position so it never
  starts past the end of a shorter one

- `Frontend` &rarr; the navigation menu scrolls on short screens (such as a phone
  held sideways) so every item stays reachable, and long entries on the `Home` page
  no longer stretch the layout out of shape

- `Server` &rarr; saving a clip no longer fails for clips with long Japanese text,
  and saved clips now use a server-generated filename that closes a security issue
  where a crafted upload name could write outside its folder

- `Server` &rarr; deleting a file also removes the jobs that used it (and is blocked
  while one of those jobs is still running), cancelling or deleting a running job no
  longer leaves the job list in a broken state, and a failed job now shows a clear
  reason

- `CLI` &rarr; `mirumoji logs -f` no longer crashes when you press Ctrl+C, and
  re-running `mirumoji up` no longer contacts Docker Hub when the images are already
  downloaded

---

## [`3.0.0`](https://github.com/svdC1/mirumoji/releases/tag/v3.0.0) - 2026-06-15

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

The [`Setup Section`](../setup/index.md) contains detailed information on all of
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
