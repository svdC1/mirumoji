"""
Defines the launcher-owned Modal app that hosts a full Mirumoji instance

`mirumoji modal deploy` lets users run the entire stack (the `FastAPI` server
and the built `React` frontend) privately on their `Modal` account

The shared deploy lifecycle functions lives in `mirumoji.modal`

info: Compute
    - The deployed `mirumoji-host` app runs the server with its CPU-Only
      `modal` transcription backend and keeps exactly one cheap, cpu-only
      container warm during its entire lifecycle

    - This guarantees that background tasks are never cut off by scaledowns,
      the in-process job queue keeps running, and the `SQLite` database only
      has one instance writing to it

    - All GPU tasks are offloaded to another modal app running in parallel
      (`mirumoji-offload`, the same one used when running the server's `modal`
      transcription backend locally)

    - The `offload` app uses the same `Modal` configuration
      variables managed by the launcher (`mirumoji config`) that are used for
      configuring the locally-run `modal` transcription backend

    - It also always scales to zero, preventing unexpected idle-GPU costs

info: Persistence
    - A named `modal.Volume` is mounted at `DATA_MOUNT`, a path separate from
      the server's data path. The server reads and writes user data on the
      container's local disk, and a background task (see `launcher.modal.app`)
      mirrors it to the volume, keeping media and database I/O off the slow
      volume FUSE layer while `Modal`'s volume commits still persist it durably

    - `mirumoji modal deploy` creates that volume in the user's `Modal`
      workspace when it doesn't exist, and `mirumoji modal stop -v` allows
      the user to delete it at any time

info: Image
    - When deployed as a full mirumoji instance to `Modal`, a single `FastAPI`
      app serves both the frontend and the server (unlike when running locally
      with docker compose, where the frontend is served by Nginx instead)

    - Because of this the Docker image that the hosted app runs is composed
      from the published CPU backend image with the published frontend build
      copied in, so `mirumoji modal deploy` always uses the latest published
      releases

    - This derived image is built at runtime using Modal's Python SDK
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import modal

from ...exceptions import ModalError
from ...modal import ensure_deployed, ensure_volume
from ..core.constants import (
    BACKEND_CPU_IMAGE,
    BACKEND_GPU_IMAGE,
    FRONTEND_IMAGE,
    MODAL_GPU_IMAGE,
    TRANSCRIBE_BACKEND_VAR,
)
from ..core.models import Backend
from .constants import (
    DATA_MOUNT,
    DATA_VOLUME_NAME,
    FRONTEND_DIR,
    FRONTEND_IMAGE_ROOT,
    HOST_APP_NAME,
    HOST_CPU_VAR,
    HOST_MAX_CONCURRENT_REQUESTS_VAR,
    HOST_MEMORY_VAR,
    HOST_ON_GPU_VAR,
    MODAL_GPU_VAR,
)

if TYPE_CHECKING:
    from fastapi import FastAPI

LOGGER = logging.getLogger(__name__)

HF_CACHE_DIR = "/root/.cache/huggingface"
"""
Where the `faster-whisper` model cache lives in the backend images

The GPU host grafts this directory from `MODAL_GPU_IMAGE` (which pre-caches the
model) onto `BACKEND_GPU_IMAGE`, so the first transcription loads it from disk
instead of downloading it
"""

DEFAULT_HOST_GPU = "A10G"
"""
The GPU a GPU host falls back to when `MODAL_GPU_VAR` is unset, matching the
`MIRUMOJI_MODAL_GPU` managed-config default
"""


def _host_image(version: str, *, gpu: bool) -> modal.Image:
    """
    Composes the `Modal` host's image from the published images at `version`

    info: CPU Host (`gpu=False`)
        Starts from `BACKEND_CPU_IMAGE` (the server stack plus the UniDic and
        Kotobase data) and copies the already-published frontend build in, so
        the deploy needs no new artifact. The container has no GPU and offloads
        transcription to the on-demand `mirumoji-offload` worker

    info: GPU Host (`gpu=True`)
        Starts from `BACKEND_GPU_IMAGE` (which adds `faster-whisper` and CUDA)
        so the `local` whisper backend can run in-process, grafts the
        pre-cached model from `MODAL_GPU_IMAGE` (which bakes it) so the first
        transcription needs no download, and copies the frontend in the same
        way. No offload worker is used in this mode

    Args:
        version (str): The published image version to compose from
        gpu (bool): Compose the GPU host image when `True`, otherwise the CPU
            one

    Returns:
        The composed host image
    """
    frontend = FRONTEND_IMAGE.format(version=version)
    copy_frontend = (
        f"COPY --from={frontend} {FRONTEND_IMAGE_ROOT} {FRONTEND_DIR}"
    )
    if not gpu:
        return modal.Image.from_registry(
            BACKEND_CPU_IMAGE.format(version=version)
        ).dockerfile_commands(copy_frontend)
    modal_gpu = MODAL_GPU_IMAGE.format(version=version)
    copy_model = f"COPY --from={modal_gpu} {HF_CACHE_DIR} {HF_CACHE_DIR}"
    return modal.Image.from_registry(
        BACKEND_GPU_IMAGE.format(version=version)
    ).dockerfile_commands(copy_frontend, copy_model)


def web() -> FastAPI:
    """
    Builds and returns the `Modal` host `FastAPI` application

    info: Container-Side
        - This runs in the `Modal` container, so it imports the app factory
          lazily and points it at the frontend copied into the image

        - The endpoint decorators (`asgi_app`, `concurrent`) are applied at
          registration in `build_host_app`, not here, so `web` stays plainly
          re-importable

    Returns:
        The host `FastAPI` application
    """
    from pathlib import Path

    from mirumoji.launcher.modal.app import create_host_app

    return create_host_app(Path(FRONTEND_DIR))


def build_host_app(
    env: dict[str, str],
    host_config: dict[str, str],
    *,
    version: str,
) -> modal.App:
    """
    Builds the deployable `Modal` host app with the user's config injected

    info: Host Modes
        - By default the web container is `CPU-Only` and runs the `modal`
          backend, offloading transcription and conversion to the on-demand
          `mirumoji-offload` GPU worker, so a GPU is paid for only while a job
          runs

        - When `MIRUMOJI_HOST_ON_GPU` is `1` the container runs on the GPU
          named by `MIRUMOJI_MODAL_GPU` with the `local` whisper backend
          in-process, so there is a single app and no offload worker, at the
          cost of an always-warm GPU. The transcribe backend is injected here
          so the CLI and the GUI never have to decide it

    info: Injected Environment
        - `env` carries the user's relevant resolved configuration (Modal
          Tokens + LLM Keys + Web Password + Modal Config) as an inline
          `Secret`, so the container behaves like a local server with the
          frontend served alongside it

        - The secret is passed inline and bundled with the deploy so that the
          user never has to manage a persistent Modal secret

    info: Resources
        - `host_config` sizes the web container itself, so `cpu` and `memory`
          are reserved rather than left to Modal's fractional default, which
          would throttle the server enough to fail its health check and get
          the container recycled

        - `max_inputs` sets how many requests the one container serves at once

    info: Function Registration
        - `web` stays a plain module-level function so `include_source` can
          re-import it cleanly by name in the container

        - The endpoint decorators (`asgi_app` wrapped in `concurrent`) and the
          deploy-time config (image, volume, secret, scaling) are applied here
          at registration, so nothing decorates `web` at module scope (a
          module-level web endpoint is re-imported as a bare `PartialFunction`
          the runtime rejects, unlike the offload worker's `Cls` path)

    info: Single Container
        - `min_containers=1` keeps one warm container so a background
          transcription is never cut off and the in-process job queue runs

        - `max_containers=1` pins the count to one, since the server holds
          in-process state and writes a single-writer SQLite file on local
          disk (mirrored to the volume), so it can't run as multiple replicas

        - The pinned count also makes a scaledown window unnecessary, so none
          is set

    Args:
        env (dict[str, str]): The environment injected into the container as an
            inline secret
        host_config (dict[str, str]): The resolved host reservations (CPU
            cores, memory in MiB, and max concurrent requests), each already
            defaulted by the caller, that size the web container
        version (str): The published image version to compose from

    Returns:
        The configured `mirumoji-host` app with `web` registered

    Raises:
        ModalError: If a host reservation in `host_config` is not a number
    """
    # A GPU host runs the local whisper backend in-process on the GPU; the
    # default CPU host offloads transcription to the separate worker. The
    # backend is decided here (not by the caller) so the CLI and GUI agree
    on_gpu = env.get(HOST_ON_GPU_VAR) == "1"
    gpu = (env.get(MODAL_GPU_VAR) or DEFAULT_HOST_GPU) if on_gpu else None
    backend = Backend.LOCAL if on_gpu else Backend.MODAL
    secret_env: dict[str, str | None] = dict(env)
    secret_env[TRANSCRIBE_BACKEND_VAR] = backend.value

    app = modal.App(HOST_APP_NAME, image=_host_image(version, gpu=on_gpu))
    volume = modal.Volume.from_name(DATA_VOLUME_NAME, create_if_missing=True)
    secret = modal.Secret.from_dict(secret_env)

    # The caller resolves these with their managed-config defaults, so every
    # key is present, but a user could still set a non-numeric value
    try:
        cpu = float(host_config[HOST_CPU_VAR])
        memory = int(host_config[HOST_MEMORY_VAR])
        max_inputs = int(host_config[HOST_MAX_CONCURRENT_REQUESTS_VAR])
    except (KeyError, ValueError) as e:
        raise ModalError(f"Invalid Host Reservation In Config: {e}") from e
    app.function(
        cpu=cpu,
        memory=memory,
        gpu=gpu,
        volumes={DATA_MOUNT: volume},
        secrets=[secret],
        min_containers=1,
        max_containers=1,
        include_source=True,
    )(modal.concurrent(max_inputs=max_inputs)(modal.asgi_app()(web)))
    return app


def ensure_host_deployed(
    env: dict[str, str],
    host_config: dict[str, str],
    *,
    version: str,
    force: bool = False,
) -> None:
    """
    Creates the `modal.Volume` if it doesn't exist and deploys the `Modal`
    host app if one of the same version is not already deployed

    Idempotent and version-tracked through `mirumoji.modal`, so it never
    duplicates the app and rolls it forward when the resolved version changes

    Args:
        env (dict[str, str]): The environment to inject into the container
        host_config (dict[str, str]): The resolved host reservations sizing the
            web container (see `build_host_app`)
        version (str): The published image version to compose from and track
        force (bool): Redeploy even when the same version is already live, to
            roll out a code or image change without a version bump

    Raises:
        ModalError: If credentials are missing or the deploy fails
    """
    ensure_volume(DATA_VOLUME_NAME)
    ensure_deployed(
        build_host_app(env, host_config, version=version),
        HOST_APP_NAME,
        version=version,
        force=force,
    )
