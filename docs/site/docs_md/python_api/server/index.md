# Overview

The Server is the `FastAPI` Backend, served by `Uvicorn` and launched with
`mirumoji server` (or `uvicorn mirumoji.server.app:app`)

It's Async-First &rarr; Routers are `async def` and blocking work is wrapped in `asyncio.to_thread()`

???+ abstract "Layout"

    - [`App`](app.md) &rarr; `FastAPI` Application + Lifespan Handler

    - [`Config`](config.md) &rarr; Runtime Configuration

    - [`Constants`](constants.md) &rarr; Shared Constants

    - [`Dependencies`](dependencies.md) &rarr; Dependency-Injection Helpers

    - [`Media`](media.md) &rarr; Media File Handling

    - [`Jobs`](jobs.md) &rarr; In-Process Async Job Queue + Worker That Backs The
      Single + Batch Operations

    - `Database` &rarr; [`SQLAlchemy Models`](db/models.md) +
      [`Repos`](db/repos.md) &rarr; Data-Access / Persistence Layer


    - `Models` &rarr; `Pydantic` Schemas
        - [`JP Dict`](models/jpdict.md) &rarr; Japanse Dictionary Data Models
        - [`Requests`](models/requests.md) &rarr; Endpoint Requests
        - [`Responses`](models/responses.md) &rarr; Endpoint Responses

    - `Processing` &rarr; Transcription / Analysis Pipeline
      *(Whisper, subtitles, text, LLM, audio, Anki)* coordinated by the [`Processor`](processing/processor.md)


    - `Routers` &rarr; HTTP Endpoints Grouped By Surface *(audio, dictionary, health, jobs, LLM, profile, video)*

    - `Modal Processing` &rarr; Optional Modal GPU-Offload Entry Points + Configuration
