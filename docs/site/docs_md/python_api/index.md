# Overview

The `mirumoji` package is the unified Python distribution that ships 2
surfaces of the project

???+ abstract "Server"
    The [`Backend REST API`](server/index.md) built with `FastAPI`. The frontend delegates all of heavy processing to it. The following are some of its core features

    - Tokenization of Japanese sentenes using `fugashi`

    - Media transcription using `faster-whisper`

    - Data persistence using `SQLAlchemy` + `sqlite3`

    - Optional routing of heavy GPU work to `Modal` cloud GPUs

    - LLM provider SDK interaction

???+ abstract "Launcher"
    Designed to be a user-friendly front-door to the `Mirumoji Docker Compose Application`, this sub-package defines a logical [`core`](launcher/core/index.md) that drives 2 user-facing applications, the [`CLI`](launcher/cli/main.md) and the [`GUI`](launcher/gui/app.md)

    !!! info "Core"
        Executes system commands using the `subprocess` module to automatically execute the necessary steps to start `mirumoji`

    !!! info "CLI"
        A CLI application built with `Typer` + `Rich` and exposed as a package script (`mirumoji`)

    !!! info "GUI"
        A `Flet` Desktop GUI that orchestrate the `Docker Compose Application`

    !!! info "Modal"
        Deploys a full, private Mirumoji instance to the user's `Modal` account (`mirumoji modal deploy`)

???+ abstract Top-Level Modules
    Four Top-Level Modules Sit Alongside Those Sub-Packages

    - [`Paths`](paths.md) &rarr; Resolved Host / Storage Paths Shared Across The Package
    - [`Exceptions`](exceptions.md) &rarr; Package's Exception Hierarchy
    - [`Log`](log.md) &rarr; Centralized Logging Setup Shared By The Server, Launcher, And GUI
    - [`Modal`](modal.md) &rarr; Shared, App-Agnostic Deploy Lifecycle For The Modal Offload Worker And The Host App

These pages are generated from the source docstrings with
[`mkdocstrings`](https://mkdocstrings.github.io/)
