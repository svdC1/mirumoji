# Modal Host Setup

Run the entire `Mirumoji` app *(the server and the frontend)* privately on your own [`Modal`](https://modal.com) account with one command, no local Docker and no public exposure

???+ question "`Modal Host` vs `Modal Transcription Backend`"
    - The [`Modal Transcription Backend`](../guides/gpu.md#modal-cloud-gpu) Runs Mirumoji `Locally` With Docker And Offloads `only` The Heavy GPU Transcription To Modal. Everything Else *(The Server, The Frontend, Your Data)* Stays On Your Machine

    - The `Modal Host` Runs `Everything` On Modal. There Is No Local Docker At All, And Your Data Lives In A [`Modal Volume`](https://modal.com/docs/guide/volumes) Instead Of A Local One

    - Both Use The Same Modal Tokens, Your [`Configuration Variables`](../cli.md#configurable-keys), And The Same GPU Offload Worker Under The Hood

## How It Works

A deploy creates two `Modal` apps and one volume in your workspace

| Resource | Role | Scaling |
| --- | --- | --- |
| `mirumoji-host` | The Server *(With The `Modal` Backend)* + Built Frontend, Served By One `FastAPI` App | `CPU-Only`, One Always-Warm Container |
| `mirumoji-offload` | Whisper Transcription + Media Conversion | `GPU`, Scales To Zero When Idle |
| `mirumoji-data` | A Persistent Data Volume Holding Your Database + Media | Persistent |

???+ question "Why Two Apps"
    - The interactive parts of Mirumoji *(watching videos, tokenizing Japanese, dictionary lookups)* are `CPU-Only`, so the host runs on a cheap CPU container which is kept warm so that background jobs are never cut off and the single-writer database always has exactly one instance

    - Only transcription or conversion needs a GPU, so the host hands that work to the `mirumoji-offload` app *(the same one the local `modal` backend uses)*, which the server creates on demand and always scales to zero when idle

    - Keeping a GPU container running idle is expensive, so this split means you only ever pay for the GPU while a transcription or conversion is actually running

!!! warning "The Cost Trade-Off"
    - The always-warm CPU host is a small standing cost, since it never scales to zero *(that is what keeps the app instantly reachable and background jobs alive)*

    - The expensive part, the GPU worker, still costs nothing while idle

    - You can configure the container's provisioned hardware with the [`Modal Host Configuration Variables`](#tuning-the-host-optional)

## Prerequisites

You'll need a [`Modal`](https://modal.com) account with your `MODAL_TOKEN_ID` + `MODAL_TOKEN_SECRET` configured. This is the same token pair that the `modal` backend uses, so if you have already set that up you are ready. If not, follow [`Get Your API Token Pair`](../guides/gpu.md#get-your-api-token-pair)


## Deploy

=== "CLI"
    ```bash
    # Set The App's Login Password
    mirumoji config set MIRUMOJI_WEB_PASSWORD <your-password> # (1)!

    mirumoji modal deploy # (2)!
    ```

    1. Skip This And Pass `--generate-password` *(`-gp`)* To `deploy` To Generate + Save A Strong One Automatically
    2. The First Deploy Composes The Image And Takes A Few Minutes. Later Deploys Are Near-Instant

    This Prints The App `URL` + The Login `Username` *(always `mirumoji`)* + `Password` + Link To The `Modal` Dashboard

=== "GUI"
    - Open the desktop launcher *(`mirumoji gui`)* and go to the `Modal Host` panel

    - Set `MIRUMOJI_WEB_PASSWORD` under `Settings` &rarr; `Modal Host` first, or tick `Generate Password` on the panel

    - Click `Deploy`. When it finishes, the panel shows the app URL as a clickable link along with the login details

!!! info "Idempotent Deploys"
    - Re-running `deploy` only rolls the app forward when the `mirumoji` version changes, so it never creates duplicates

    - Pass `--force` *(`-f`)* to redeploy the same version through the CLI

## Open It

Open The Printed URL. Your Browser Will Show A Login Prompt

- `Username` &rarr; `mirumoji`

- `Password` &rarr; The Value Of `MIRUMOJI_WEB_PASSWORD`

Once you log in, the whole app loads and works exactly like a local install, with a real, publicly trusted certificate *(Modal serves everything over HTTPS on a `*.modal.run` address)*, so there is no certificate to install as there is when serving on LAN ips

???+ question "Why A Browser Login Prompt"
    - The hosted app is protected with [`HTTP Basic Auth`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Authentication#basic_authentication_scheme), which is the only scheme a browser handles natively at the edge

    - A `401` makes the browser show its own prompt and then attach the credentials to `every` later request *(the page, the assets, the API, the uploads)* automatically

    - That gates the whole app without a login page or any change to the server or frontend, which keeps `Mirumoji` free of auth for its *primary* use as a self-hosted tool

    - After the first login the host sets a persistent, `HttpOnly` cookie and accepts it in place of the prompt, so an installed `iOS` `PWA` *(which drops the `Basic Auth` credential cache whenever it is closed)* does not re-prompt for the password on every reopen. Changing `MIRUMOJI_WEB_PASSWORD` invalidates it

    - See [`Sharing Outside Your Network`](../guides/sharing.md#modal-host-private-full-deploy) for how this compares to the other sharing options and how to add identity-based access if you need it

## Your Data

Unlike a local install *(which keeps your data in local Docker volumes)*, the hosted app stores your media and database in the `mirumoji-data` [`Modal Volume`](https://modal.com/docs/guide/volumes), created automatically on the first deploy

???+ question "How It Stays Fast And Durable"
    - The host does not read and write directly on the volume, whose network layer is slow for the many small, random reads that video playback and the database make. It operates on the container's local disk and mirrors every change to the volume in the background

    - `Modal` commits the volume as the app runs and on shutdown, and the host restores it into the container on every start, so your data survives a redeploy, a stop, or a spot preemption

=== "Back It Up"
    Download everything in the volume to a local folder at any time

    ```bash
    mirumoji modal download-data [DESTINATION] # (1)!
    ```

    1. Defaults To A `mirumoji-data` Folder In The Current Directory. Re-downloading Overwrites The Existing Copies

=== "Delete It"
    ```bash
    mirumoji modal down -v # (1)!
    ```

    1. Stops The App And Permanently Deletes The Volume. This Erases The Hosted Profiles, Media, And Database

## Tuning The Host (Optional)

The host container reserves `CPU` and `Memory` so the server never gets throttled into a failed health check. The defaults are a sensible balance, but you can adjust them

| Variable | Default | What It Does |
| --- | --- | --- |
| `MIRUMOJI_HOST_CPU` | `2` | CPU Cores Reserved For The Always-Warm Web Container *(Higher Is Faster But Costs More)* |
| `MIRUMOJI_HOST_MEMORY` | `4096` | Memory In MiB Reserved For The Web Container *(Higher Avoids Restarts But Costs More)* |
| `MIRUMOJI_HOST_MAX_CONCURRENT_REQUESTS` | `100` | How Many Requests The One Container Serves At Once |

The GPU worker is tuned by the same [`Modal Variables`](../guides/gpu.md#tuning-modal-optional) that the local `modal` backend uses *(`MIRUMOJI_MODAL_GPU`, `MIRUMOJI_MODAL_SCALEDOWN_WINDOW`, ...)*. Change any of these, then redeploy for them to take effect

## Managing The Deployment

```bash
mirumoji modal status # (1)!
mirumoji modal down # (2)!
mirumoji modal down --volume # (3)!
```

1. Show The Host App, The Data Volume, And The URLs
2. Stop The Host App *(Your Data Volume Is Kept)*
3. Stop The Host App + Delete The Data Volume

The GPU offload worker is owned by the server, which stops it during shutdown, so `modal down` does not touch it and `modal status` does not list it

???+ danger "This Is A Publicly Reachable Service"
    - A Modal web endpoint is reachable by anyone who has both the URL and the password, so use a strong `MIRUMOJI_WEB_PASSWORD` *(letting `--generate-password` create one is the safe default)*

    - Anyone who can log in can read and modify the hosted profiles, media, and clips

    - For identity-based access instead of a shared password, see the [`Sharing`](../guides/sharing.md) guide
