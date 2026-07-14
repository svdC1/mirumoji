"""
Defines the constants for the launcher-owned Modal host deploy

info: Pre-Defined Values
    - The name of the deployed `Modal` app and the name of the `web function`
      that runs the `FastAPI` application
      (`HOST_APP_NAME`, `WEB_FUNCTION_NAME`)

    - The name of the persistent `Modal` volume used to store user data and the
      location in which its mounted in the `web function's` container
      (`DATA_VOLUME_NAME`, `DATA_MOUNT`)

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
      (`HOST_MAX_CONCURRENT_REQUESTS_VAR`, `HOST_CPU_VAR`,
      `HOST_MEMORY_VAR`)
"""

HOST_APP_NAME = "mirumoji-host"
"""
The deployed host app's name on the user's Modal workspace
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

DATA_MOUNT = "/root/.local/share/mirumoji"
"""
Where the persistent `Volume` mounts, matching the container's platformdirs
`user_data_path` so the server's storage lands on the volume unchanged (the
same path the Docker `data` volume uses)
"""

STATE_MOUNT = f"{DATA_MOUNT}/state"
"""
Value for the container's `XDG_STATE_HOME`, kept under `DATA_MOUNT`

question: Why
    - On Linux, `platformdirs` places the log directory under the state dir
      (`XDG_STATE_HOME`), which is a separate top-level path from the data dir,
      so server logs would otherwise land on ephemeral container storage
      instead of the mounted volume

    - Pointing `XDG_STATE_HOME` beneath the volume mount makes the logs persist
      on the volume alongside the database and media, using the standard XDG
      mechanism rather than a mirumoji-specific path override
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
