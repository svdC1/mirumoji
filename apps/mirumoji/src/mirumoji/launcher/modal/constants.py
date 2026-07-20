"""
Defines the constants for the launcher-owned Modal host deploy

info: Pre-Defined Values
    - The name of the deployed `Modal` app and the name of the `web function`
      that runs the `FastAPI` application
      (`HOST_APP_NAME`, `WEB_FUNCTION_NAME`)

    - The name of the persistent `Modal` volume used to store user data, the
      separate path at which it is mounted, and the local-disk path the server
      reads and writes and the syncer mirrors to the volume
      (`DATA_VOLUME_NAME`, `DATA_MOUNT`, `CONTAINER_CACHE`)

    - Where the built frontend lives inside the Docker image run by the
      `web function` and where the frontend lives inside mirumoji's published
      frontend Docker image (`FRONTEND_DIR`, `FRONTEND_IMAGE_ROOT`)

    - How many requests the the `web function` can serve simultaneously
      (`MAX_CONCURRENT_REQUESTS`)

    - The pre-defined username used for the `Basic Auth` and the name of the
      managed environment variable containing the user-defined `Basic Auth`
      password which gurads the deployed app (`WEB_USERNAME`,
      `WEB_PASSWORD_ENV`)

    - Managed environment variables defining the hardware capability to request
      for the container that runs the `web function`
      (`HOST_MAX_CONCURRENT_REQUESTS_VAR`, `HOST_CPU_VAR`, `HOST_MEMORY_VAR`)

    - The GPU / preemptibility host-mode keys (`MIRUMOJI_HOST_ON_GPU`,
      `MIRUMOJI_MODAL_GPU`, `MIRUMOJI_HOST_NONPREEMPTIBLE`) live in
      `core.constants` and resolve through `core.envfile`
"""

HOST_APP_NAME = "mirumoji-host"
"""
The deployed host app's name on the user's Modal workspace
"""

MODAL_LOGS_MAX_TAIL = 20000
"""
The largest `--tail` the `modal app logs` CLI accepts

Passing more is rejected with a usage error, so the launcher bounds its own
option here and reports a clean message instead of surfacing modal's raw usage
text
"""

HOST_MODE_KEY = "mirumoji-host-mode"
"""
Modal app tag holding a digest of the host's deploy-time configuration (GPU vs
CPU, preemptibility, and the CPU / memory / concurrency reservations)

Passed to `mirumoji.modal.ensure_deployed` as an extra identity tag, so
changing the host mode or a reservation at the same version forces a redeploy
instead of matching the live app and silently doing nothing
"""

WEB_FUNCTION_NAME = "web"
"""
The host app's web endpoint name (the `web` function), used for
`Function.from_name` URL lookups
"""

DATA_VOLUME_NAME = "mirumoji-data"
"""
The persistent `modal.Volume` name backing the database and media
"""

DATA_MOUNT = "/opt/mirumoji/volume_mnt"
"""
Where the persistent `Volume` mounts inside the container

The volume is mounted in the container at this path only so that
a background task can utilise the mount's FUSE syncing to persist
user data from the `CONTAINER_CACHE` to the volume on file-system
changes. Therefore, this directory is always kept in sync with
`CONTAINER_CACHE` throughout the application's lifespan
"""

CONTAINER_CACHE = "/root/.local/share/mirumoji"
"""
Where the mirumoji user data lives inside the container, matching the
container's platformdirs `user_data_path`

info: Data Handling
    - Instead of mounting the persistent volume directly on this path,
      a background task watches this directory and keeps the volume
      in sync with it

    - This allows the application to serve files and perform database
      operations directly on the container's NVMe, avoiding network
      latency on file operations, which would considerably slow down
      the application
"""

FRONTEND_DIR = "/opt/mirumoji/frontend"
"""
Where the built frontend is copied inside the composed image
"""

FRONTEND_IMAGE_ROOT = "/usr/share/nginx/html"
"""
Where the published frontend image serves the build from (nginx's web root),
the source of the `COPY --from` that grafts it into the host image
"""

HOST_MAX_CONCURRENT_REQUESTS_VAR = "MIRUMOJI_HOST_MAX_CONCURRENT_REQUESTS"
"""
Managed config key setting how many requests the web container serves at once
"""

HOST_CPU_VAR = "MIRUMOJI_HOST_CPU"
"""
Managed config key setting the CPU cores reserved for the web container
"""

HOST_MEMORY_VAR = "MIRUMOJI_HOST_MEMORY"
"""
Managed config key setting the memory (MiB) reserved for the web container
"""

WEB_USERNAME = "mirumoji"
"""
The username that the browser `HTTP Basic Auth` prompt expects
"""

WEB_PASSWORD_ENV = "MIRUMOJI_WEB_PASSWORD"
"""
Environment variable carrying the host app's Basic Auth password into the
container, matching the `MIRUMOJI_WEB_PASSWORD` managed config key
"""
