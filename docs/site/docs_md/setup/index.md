# Setup

There Are `3 Ways` To Get Mirumoji Running

Pick The One That Fits You

<div class="grid cards" markdown>

- :material-monitor: **[GUI Setup](gui.md)**

    Downlaod Desktop Launcher For Your Platform To Start, Stop, and
    Configure Mirumoji &rarr; `Easiest`

- :material-console: **[CLI Setup](cli.md)**

    Install With `pip` And Run The Docker Compose Applicatin With `mirumoji up`
    &rarr; `For Those Who Prefer The Terminal`

- :material-docker: **[Manual Setup](manual.md)**

    Run The Docker Compose Commands Yourself, No Launcher &rarr; `More Configuration`

</div>

## Prerequisites

| Requirement | Needed for | Notes |
| --- | --- | --- |
| **Docker** + **Compose V2** | All Setups | Download The Cross-Platform [`Docker Desktop`](https://docs.docker.com/desktop/) *(Or [`Docker Engine`](https://docs.docker.com/engine/install/) + [`Compose Plugin`](https://docs.docker.com/compose/install/linux/) On Linux)* |
| **Python 3.10+** | CLI Setup | Only To Install The [`mirumoji`](https://pypi.org/project/mirumoji/#description) Launcher From PyPI. |
| **NVIDIA GPU + [`Container Toolkit`](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)** | `Local` Transcription Backend | Lets The Backend Run [`faster-whisper`](https://github.com/SYSTRAN/faster-whisper) on your GPU. |
| **A [`Modal`](https://modal.com) Account** | `Modal` Transcription Backend | To Offload Ttranscription To Cloud GPUs For CPU-Only Setups |

!!! tip "Check Your Machine"
    With the `CLI` installed, run `mirumoji doctor` to see which dependencies
    you're missing

## Transcription Backends

Transcription / Conversion are terribly slow for long media when running on a CPU

Mirumoji lets you choose in what `GPU` that work runs

=== "Modal"
    - Offloads the work to **[`Modal`](https://modal.com)** cloud GPU containers
    
    - Your machine does `not` need a GPU to run this backend
    
    - Requires a Modal account's API Tokens &rarr; `MODAL_TOKEN_ID` + `MODAL_TOKEN_SECRET`

    ```bash
    # CLI Configuration For Modal Transcription Backend
    mirumoji config set MIRUMOJI_TRANSCRIBE_BACKEND modal
    mirumoji config set MODAL_TOKEN_ID <your-token-id>
    mirumoji config set MODAL_TOKEN_SECRET <your-token-secret>
    ```

=== "Local"
    - Runs the work on `your` NVIDIA GPU  via the Container Toolkit
    
    - No Cloud Account Needed

    ```bash
    # CLI Configuration For Local Transcription Backend
    mirumoji config set MIRUMOJI_TRANSCRIBE_BACKEND local
    ```

???+ tip "Configuration"
    - The Launcher (CLI + GUI) remembers your choice in its [`Managed Config File`](cli.md#configuration),
      so you only need to set it once
    
    - `Modal` is the default because it works on any machine

    - See [`Using a GPU`](../guides/gpu.md) for a full walkthrough of both backends

## LLM Features (Optional)

Provide one of these keys to unlock AI breakdowns for words and sentences + refinement for subtitles

When none are set, these features are simply disabled

```bash
# Configuring LLM Provider Keys Using The CLI
mirumoji config set OPENAI_API_KEY sk-...
mirumoji config set ANTHROPIC_API_KEY sk-ant-...
mirumoji config set GEMINI_API_KEY ...

# Any OpenAI-Compatible LLM Server Endpoint
mirumoji config set MIRUMOJI_LLM_BASE_URL https://my-endpoint/v1
mirumoji config set MIRUMOJI_LLM_API_KEY ...
```

!!! tip "Configuration Variables"
    See the [`CLI Reference`](../cli.md#configuration-commands) for every configurable variable

## Opening Mirumoji

Once the Docker Compose Applicatin is running, the frontend is served over HTTPS

???+ Access Links
    - Host Machine &rarr; [`https://localhost`](https://localhost)
    - Another Device On The Host's Network &rarr; `https://<your-machines-IPv4-LAN-IP>`

!!! warning "Self-Signed Certificate"
    - The frontend generates a self-signed certificate for your LAN IP at startup,
      so your browser will show a one-time "not private" warning
    
    - That's expected on a local network and poses no security risk. You can safely continue past it.
    
    - To reach Mirumoji from `outside` your network, see [`Sharing Outside Your Network`](../guides/sharing.md).
