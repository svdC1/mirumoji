# Overview

The `mirumoji` package is the unified Python distribution that ships 2
surfaces of the project

- [`Server`](server/index.md) &rarr; The FastAPI backend that tokenizes Japanese, runs Whisper
  transcription, manages profiles, and exports Anki decks

- `Launcher` &rarr; The  `Typer` / `Rich` CLI (`mirumoji`) + `Flet` Desktop GUI
  (`mirumoji gui`) that orchestrate the `Docker Compose Application`. See the `CLI`, `Core`,
  and `GUI` Sections

Two Top-Level Modules Sit Alongside Those Sub-Packages

- [`Paths`](paths.md) &rarr; Resolved Host / Storage Paths Shared Across The Package
- [`Exceptions`](exceptions.md) &rarr; Package's Exception Hierarchy

These pages are generated from the source docstrings with
[`mkdocstrings`](https://mkdocstrings.github.io/)
