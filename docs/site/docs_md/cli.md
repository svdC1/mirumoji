# CLI Reference

This section explains all commands exposed by the `mirumoji` CLI

Run `mirumoji --help`, or `mirumoji <command> --help`, for the same information in your terminal

```bash
mirumoji [COMMAND] [OPTIONS]
```

!!! tip "Installed Version"
    `mirumoji --version` prints the installed launcher version and exits *(distinct from the per-command `--image-version`, which pins the published image version)*

???+ abstract "Deploy-Option Resolution"
    The `Transcription Backend`, `Image Source`, and `Image Version` deploy options are each evaluated in the following order of precedence. If one of the upper items is missing, the one right below it is used, until reaching a base default value

    !!! info "Transcription Backend"
        - `Flag` (`--transcribe / -t`)

        - `Saved Configuration File` (`mirumoji config show`)

        - `Base Default` (`modal`)

    !!! info "Image Source"
        - `Flag` (`--build / --pull`, on `up` and `render`)

        - `Saved Configuration File` (`mirumoji config show`)

        - `Base Default` (`pull`)

    !!! info "Image Version"
        - `Flag` (`--image-version`)

        - `Saved Configuration File` (`MIRUMOJI_IMAGE_VERSION`)

        - `Shell Environment` (`MIRUMOJI_IMAGE_VERSION`)

        - `Base Default` (The Installed Package Version)

## Lifecycle Commands

### `up`

Starts the Mirumoji `Docker Compose` Application

```bash
mirumoji up [OPTIONS]
```

| Option | Default | Description |
| --- | --- | --- |
| `-t`, `--transcribe [local \| modal]` | Saved Config, Else `modal` | Transcription Backend |
| `--build` / `--pull` | Saved Config, Else `--pull` | Build Images Locally / Pull Pre-Buil From Docker Hub |
| `-d`, `--detach` / `--foreground` | `--detach` | Run In The Background / Stream In The Foreground |
| `--image-version` | Saved Config, Else Installed Version | Use This Published Image Version |

??? question "What It Does"
    - Resolves Your `Transcription Backend` / `Image Source` / `Image Version` Options

    - Validates That Required Keys Are Configured And External Dependencies Are Present

    - Discovers Your IPv4 LAN IP For The Self-Signed Frontend Certificate

    - Builds / Pulls Images

    - Runs `docker compose up`

    - Prints local and LAN URLs

### `down`

Stops The Docker Compose Application

```bash
mirumoji down [OPTIONS]
```

| Option | Default | Description |
| --- | --- | --- |
| `-v`, `--volumes` / `--keep-volumes` | `--keep-volumes` | Also Delete Data Bolumes *(profiles, media, database)* |
| `-y`, `--yes` | off | Skip Confirmation Prompt When Deleting Volumes|

### `reset`

Deletes Mirumoji's Local Data Folder From This Machine *(media, database, cached builds, config, logs)*. Docker Data Volumes Are Not Touched &rarr; Use `down --volumes` For Those

```bash
mirumoji reset [OPTIONS]
```

| Option | Default | Description |
| --- | --- | --- |
| `-kc`, `--keep-config` | off | Preserve The Config File *(Your LLM / Modal Keys)* |
| `-kl`, `--keep-logs` | off | Preserve The Log Files |
| `-y`, `--yes` | off | Skip The Confirmation Prompt |

### `status`

Shows The Running Docker Compose Services + Their Health As A Table

```bash
mirumoji status
```

### `logs`

Streams Logs From The Whole Docker Compose Application Or A Single Service

```bash
mirumoji logs [SERVICE] [OPTIONS]
```

| Argument / Option | Default | Description |
| --- | --- | --- |
| `SERVICE` | all | Scope To One Service (`frontend` or `backend`) |
| `-f`, `--follow` | off | Follow New Output |
| `-t`, `--tail N` | all | Show Only Last `N` Lines |

### `pull`

Pulls Pre-Built Images From Docker Hub For The Chosen Transcription Backend

```bash
mirumoji pull [OPTIONS]
```

| Option | Default | Description |
| --- | --- | --- |
| `-t`, `--transcribe [local \| modal]` | Saved Config, Else `modal` | Transcription Backend |
| `--image-version` | Saved Config, Else Installed Version | Pull This Published Image Version |

### `build`

Clones / Updates The Managed `Mirumoji GitHub Repository` Checkout At A Release Tag And Builds The Frontend + Backend Images Locally For The Chosen Backend

```bash
mirumoji build [OPTIONS]
```

| Option | Default | Description |
| --- | --- | --- |
| `-t`, `--transcribe [local \| modal]` | Saved Config, Else `modal` | Transcription Backend |
| `--image-version` | Saved Config, Else Installed Version | Build This Version's Tagged Source *(Its `v<version>` Git Tag)* |

### `doctor`

Reports The Status Of Every External Dependency (`Docker`, `Compose`, `Git`, `NVIDIA GPU` + `NVIDIA Contianer Toolkit`, `Flet`, `Flutter`)

```bash
mirumoji doctor
```

### `gui`

Launches The Desktop GUI Launcher

Requires The `gui` Extra *(`pip install mirumoji[gui]`)*

```bash
mirumoji gui
```

### `render`

Writes A Resolved `docker-compose.yaml` From The Packaged Template For A Chosen
Transcription Backend And Image Source Without Running The Applocation

Used for [`Manual Installs`](setup/manual.md)

```bash
mirumoji render [OPTIONS]
```

| Option | Default | Description |
| --- | --- | --- |
| `-t`, `--transcribe [local \| modal]` | Prompts | Tranascription Backend To Target |
| `--build` / `--pull` | `--pull` | Reference Locally Built Tags Or Docker Hub Images |
| `--image-version` | Saved Config, Else Installed Version | Pin The Image Version |
| `-o`, `--output PATH` | `docker-compose.yaml` | Where To Write The File |

## Development Commands

### `dev server`

Runs The `FastAPI` Server Directly With `uvicorn` (no Docker), Using The App Factory

Intended For Development &rarr; Requires The `server` Extra *(`pip install mirumoji[server]`)*

```bash
mirumoji dev server [OPTIONS]
```

| Option | Default | Description |
| --- | --- | --- |
| `--host` | `0.0.0.0` | Interface To Bind |
| `--port` | `8000` | Port To Listen On |
| `--reload` | off | Reload On Code Changes |

### `dev up`

Builds The Frontend + Backend Images From A Local `Mirumoji` Repo Checkout And Runs The Docker Compose Application, Without Updating The Checkout

Intended For Development &rarr; Builds From An Arbitrary Path Rather Than The Managed Checkout That `build` Uses

```bash
mirumoji dev up [OPTIONS]
```

| Option | Default | Description |
| --- | --- | --- |
| `-t`, `--transcribe [local \| modal]` | Saved Config, Else `modal` | Transcription Backend |
| `-p`, `--path PATH` | `Path.cwd()` | Path To The Local Mirumoji Repo Checkout |
| `-d`, `--detach` / `--foreground` | `--detach` | Run In The Background / Stream In The Foreground |



## Modal Host Commands

Deploy And Manage A Full, Private `Mirumoji` Instance On Your Own `Modal` Account

???+ info "Difference From The [`Modal Transcription Backend`](guides/gpu.md#modal-cloud-gpu)"
    - The `Modal` transcription backend *only offloads GPU work*

    - These commands run the *whole* app *(the server and the frontend)* on `Modal`, so there is no local Docker at all

    - See the [`Modal Host Setup Guide`](setup/modal-host.md) for the full walkthrough

???+ abstract "Requirements"
    - A [`Modal`](https://modal.com) Account

    - The Account's `MODAL_TOKEN_ID` + `MODAL_TOKEN_SECRET` Configured *(Same As The [`Modal Transcription Backend`](guides/gpu.md#modal-cloud-gpu))*

### `modal deploy`

Deploys A Fully Functional Mirumoji App To Your Modal Account, Gated By [`HTTP Basic Auth`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Authentication#basic_authentication_scheme)

```bash
mirumoji modal deploy [OPTIONS]
```

| Option | Default | Description |
| --- | --- | --- |
| `-gp`, `--generate-password` | off | Generate A Login Password When `MIRUMOJI_WEB_PASSWORD` Is Not Set And Save It To The Config |
| `-f`, `--force` | off | Redeploy Even If The Same Version Is Already Live |
| `--image-version` | Saved Config, Else Installed Version | Deploy This Published Image Version |
| `--host-on-gpu` / `--no-host-on-gpu` | Saved Config | Run The Host On A GPU With Whisper In-Process *(Overrides `MIRUMOJI_HOST_ON_GPU`; The GPU Type Comes From `MIRUMOJI_MODAL_GPU`)* |
| `--nonpreemptible` / `--preemptible` | Saved Config | Run The CPU Host On Non-Preemptible Capacity *(Overrides `MIRUMOJI_HOST_NONPREEMPTIBLE`; Not For A GPU Host)* |

??? question "What It Does"
    - Resolves Your [`Managed Config`](#configuration-commands) *(LLM Keys, Modal Config, Host Reservations)* And Injects It Into The Container As A [`Modal Secret`](https://modal.com/docs/guide/secrets)

    - Composes The Host Image From The Published Backend *(CPU, Or GPU For A GPU Host)* + `Frontend` Images

    - Creates *(or Reuses)* The `mirumoji-data` Volume That Persists Your Database And Media

    - Deploys The `mirumoji-host` App *(Idempotent &rarr; A Matching Version Is A No-Op Unless You Pass `--force`)*

    - Prints The App URL, The Login Username *(`mirumoji`)* + Password + The Modal Dashboard Link

!!! info "Login"
    - The Username Is Always `mirumoji`

    - The `MIRUMOJI_WEB_PASSWORD` Configuration Variable Is The Password

    - Set The Password With `mirumoji config set MIRUMOJI_WEB_PASSWORD ***`

    - Alternatively, Pass `--generate-password` To Create + Save A Strong One On The First Deploy

    - A Managed Configuration Value Takes Precedence Over A Environment Variable In The Current Shell

!!! info "The Offload Worker"
    - By Default The Host Runs On A `CPU-Only` Container And Offloads GPU Tasks To The Same `mirumoji-offload` App That The [`Modal Transcription Backend`](guides/gpu.md#modal-cloud-gpu) Uses

    - The Server Creates `mirumoji-offload` On Demand And Always Scales To Zero, So An Idle GPU Never Costs You

    - Set `MIRUMOJI_HOST_ON_GPU=1` To Instead Run The Host Itself On A GPU With `faster-whisper` In-Process, So There Is No Offload Worker *(The GPU Is Then Always-Warm)*

!!! info "Configuring The Container"
    - You Can Configure The Provisioned Container That Runs The App With The [`Modal Host Configuration Variables`](#configurable-keys)

    - You Set Its `CPU Core Count`, `Memory (MiB)`, And `Max Concurrent Requests`, Whether It Runs On A GPU (`MIRUMOJI_HOST_ON_GPU`), And Whether It Uses Non-Preemptible Capacity (`MIRUMOJI_HOST_NONPREEMPTIBLE`)

### `modal status`

Shows The State Of The `mirumoji-host` App And Its `mirumoji-data` Volume

```bash
mirumoji modal status
```

### `modal logs`

Fetches Or Live-Streams The Hosted `mirumoji-host` App's Logs *(Useful For Diagnosing A Deploy Or A Failing Job On The Host)*

```bash
mirumoji modal logs [OPTIONS]
```

| Option | Default | Description |
| --- | --- | --- |
| `-n`, `--tail N` | `100` | How Many Recent Log Entries To Fetch |
| `-f`, `--follow` | off | Live-Stream The Logs Until Interrupted *(Ctrl-C)* |

### `modal down`

Stops The Hosted App And Optionally Deletes Its Data Volume

```bash
mirumoji modal down [OPTIONS]
```

| Option | Default | Description |
| --- | --- | --- |
| `-v`, `--volume` / `--keep-volume` | `--keep-volume` | Also Delete The Data Volume *(profiles, media, database)* |
| `-y`, `--yes` | off | Skip The Confirmation Prompt When Deleting The Volume |

!!! warning "Volume Deletion Is Permanent"
    - The volume is deleted only when `--volume` is passed, and only after the app is stopped *(Modal refuses to   delete a volume mounted on a deployed app)*

    - Deleting it permanently erases the hosted profiles, media, and database

### `modal download-data`

Downloads The Hosted `mirumoji-data` Volume To A Local Directory For Backup Or Inspection

```bash
mirumoji modal download-data [DESTINATION]
```

| Argument | Default | Description |
| --- | --- | --- |
| `DESTINATION` | `mirumoji-data` | Local Directory To Download The Hosted Data Into *(re-downloading overwrites the existing copies)* |

## Configuration Commands

???+ info "Managed Configuration File"
    - All Settings Are Kept In A Single Managed `.env` File

    - It's Changed `Only` Through The Following Commands

    - Run Commands (`up`, `build`, `pull`) Never Modify It

```bash
mirumoji config set <KEY> <VALUE> # (1)!
mirumoji config delete <KEY> # (2)!
mirumoji config show # (3)!
mirumoji config path # (4)!
mirumoji config import <PATH> # (5)!
mirumoji config clear # (6)!
```

1. Set Or Update One Variable. Rejects Unknown Keys, and Validates The Value Of Deployment
Keys Against Their Allowed Options
2. Remove One Variable
3. Print Current Config *(Secrets Masked. Pass `--raw` To Unmask Them, Or `--json` For Unmasked `JSON` Output)*
4. Print The Location Of The Configuration File
5. Merge an Existing `.env` File
6. Remove Everything


### Configurable Keys

=== "Deployment"
    | Key | Values | Default | Description |
    | --- | --- | --- | --- |
    | `MIRUMOJI_TRANSCRIBE_BACKEND` | `local`, `modal` | `modal` | Where Transcription / Conversion Runs |
    | `MIRUMOJI_IMAGE_SOURCE` | `pull`, `build` | `pull` | Pull Pre-Built Images / Build Images Locally |
    | `MIRUMOJI_IMAGE_VERSION` | Any Published Version | Installed Version | Pin The Published Image Version The Launcher Pulls, Composes, Or Builds |

=== "LLM providers"
    All Optional &rarr; Set Any Or All To Enable LLM Features

    | Key | Description |
    | --- | --- |
    | `OPENAI_API_KEY` | Enable GPT Models |
    | `ANTHROPIC_API_KEY` | Enable Claude Models |
    | `GEMINI_API_KEY` | Enable Gemini Models |
    | `MIRUMOJI_LLM_BASE_URL` | Use A Custom OpenAI-Compatible LLM Server Endpoint |
    | `MIRUMOJI_LLM_API_KEY` | Key For The Custom Endpoint Above (Leave Empty If Not Applicable) |

=== "Modal"
    Required Only For The `modal` Transcription Backend

    | Key | Default | Description |
    | --- | --- | --- |
    | `MODAL_TOKEN_ID` | Required | Modal Token ID |
    | `MODAL_TOKEN_SECRET` | Required | Modal Token Secret |
    | `MIRUMOJI_MODAL_GPU` | `A10G` | GPU Type To Use In The Modal Containers |
    | `MIRUMOJI_MODAL_SCALEDOWN_WINDOW` | `60` | Seconds To Keep An Idle Modal Container Warm Before Scaling Down |
    | `MODAL_FORCE_BUILD` | `0` | Force Modal to Rebuild Its Cached App Image |

=== "Modal Host"
    Used Only By The [`modal deploy`](#modal-deploy) Command. The Login Username Is Always `mirumoji`, Only The Password Is Configurable

    | Key | Default | Description |
    | --- | --- | --- |
    | `MIRUMOJI_WEB_PASSWORD` | Generated | Login Password For The Hosted App (Generated On First Deploy When Unset) |
    | `MIRUMOJI_HOST_CPU` | `2` | CPU Cores Reserved For The Always-Warm Web Container (Higher Is Faster But Costs More) |
    | `MIRUMOJI_HOST_MEMORY` | `4096` | Memory (MiB) Reserved For The Always-Warm Web Container |
    | `MIRUMOJI_HOST_MAX_CONCURRENT_REQUESTS` | `100` | How Many Requests The Web Container Serves At Once |
    | `MIRUMOJI_HOST_ON_GPU` | `0` | Run The Host On A GPU With Whisper In-Process (`1`) Instead Of A CPU Host + Offload Worker (`0`). Uses `MIRUMOJI_MODAL_GPU` For The GPU Type |
    | `MIRUMOJI_HOST_NONPREEMPTIBLE` | `0` | Run The CPU Host On Non-Preemptible Capacity (`1`) At A 3x Cost. Not Available With A GPU Host |

=== "Advanced"
    Optional Overrides &rarr; The Server Has Sensible Defaults For All Of These

    | Key | Description |
    | --- | --- |
    | `MIRUMOJI_LOGGING_LEVEL` | Python Logging Level For The Backend |
    | `MIRUMOJI_MODAL_IMAGE` | Docker Hub Image The Modal GPU Containers Run *(Default `svdc1/mirumoji-modal-gpu:<version>`)* |
    | `MIRUMOJI_MAX_LLM_CONCURRENCY` | How Many LLM Requests Run At Once When Fixing A Batch Of Subtitles (Default `4`) |
    | `MIRUMOJI_SRT_DEFAULT_SYS_MSG` | Default LLM System Message For Subtitle Refinement |
    | `MIRUMOJI_BREAKDOWN_DEFAULT_SYS_MSG` | Default LLM System Message For Word Breakdowns |

### Examples

```bash

mirumoji config set MIRUMOJI_TRANSCRIBE_BACKEND local
mirumoji config set MODAL_TOKEN_ID abc123
mirumoji config show
```
