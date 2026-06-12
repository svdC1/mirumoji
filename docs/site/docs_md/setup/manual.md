# Manual Setup

This section will teach you how to get mirumoji running without using any of the `Launchers`

You can run the `Docker Compose Application` yourself with the pre-built images published
to `Docker Hub` or with `Locally Built` images


??? question "When To Use This"
    - Most users should use the [`CLI`](cli.md) or [`Desktop Launcher`](gui.md) setup
    
    - They handle the `Compose File`, `IPv4 LAN IP Reoslution`, and `Configuration` automatically
    
    - Use a manual install when you want full control of the `Compose File`, for example, to add a reverse-proxy or change ports


## Get a Compose File

- The `Compose File` is generated from a packaged template for your chosen
  [`Transcription Backend`](index.md#transcription-backends) and `Image Source`

- The simplest way to produce a correct one is the CLI's `mirumoji render` command, which writes the file and
  exits without starting anything

```bash
pip install mirumoji
mirumoji render --transcribe modal --pull --output docker-compose.yaml
```

???+ info "Flags"
    - `--transcribe modal|local` &rarr; Which Transcription Backend The File Targets

    - `--pull` &rarr; Reference The Pre-Built Docker Hub Images

    - `--output` &rarr; Where To Write The File

This gives you a plain `docker-compose.yaml` that you can read, edit, and run with
ordinary Docker tooling

## Create an Environment File

???+ abstract "Passing Configurations To The Server"
    - The Compose file reads its configuration from environment variables
    
    - Every value has a `${VAR:-default}` fallback, so you only set what your backend needs


```bash title="Create A .env Next To Your Compose File"
# (1)!
MODAL_TOKEN_ID=your-token-id
MODAL_TOKEN_SECRET=your-token-secret

# (2)!
OPENAI_API_KEY=sk-...

# (3)!
HOST_LAN_IP=192.168.1.50
```

1. Required For The `Modal` Backend (Omit For The `Local` Backend)
2. Optional LLM Features
3. Set This To Your Machine's `IPv4 LAN IP` So That The Frontend's HTTPS Certificate + Other Devices On Your Network Can Reach It. Defaults to `127.0.0.1` (Host Only)

??? tip "Finding Your IPv4 LAN IP"
    === "Windows"
        ```bash
        ipconfig
        ```
        
    === "MacOS / Linux"
        ```bash
        ip addr
        # Or ifconfig
        ```

View The [`Full List Of Accepted Variables`](../cli.md#configuration-commands)

## Start Docker Compose

```bash
docker compose --env-file .env up -d
```

The application should be live on your [`https://localhost`](https://localhost), and on `https://<HOST_LAN_IP>` from another device in your local network

### Ports

| Service | Port | Purpose |
| --- | --- | --- |
| frontend | `80` | HTTP &rarr; Redirects to HTTPS |
| frontend | `443` | HTTPS *(Self-Signed Certificate Built For `HOST_LAN_IP`)* |
| backend | `8000` | FastAPI Server |

??? info "Backend Access"
    - The `frontend` service runs an `Nginx` server, which serves the `React` app via HTTPS + the self-signed     certificate
    
    - This `Nginx` server also configures a reverse-proxy for the application's internal Docker network pointing to the `backend` server under `https://localhost/api`, so the FastAPI can be accessed through there as well

### Data

???+ info "Docker Volumes"
    - Your profiles, media, and database live in the `data` volume
    
    - Application logs live in the `logs` volume
    
    - These survive both restarts and version bumps
    
    - Removing those volumes deletes your data

```bash
docker compose down            # stop, keep data
docker compose down --volumes  # stop and delete all data
```

## Building Images Locally

To build the Docker Images from source instead of pulling the pre-built ones from `Docker Hub`, use `mirumoji render` with `--build` and run `docker compose build` from a clone of the [`Mirumoji Repository`](https://github.com/svdC1/mirumoji) before running `docker compose up`

The [`CLI Setup`](cli.md) automates this end-to-end with `mirumoji up --build`
