"""
Shared `Modal` app and container image used by all `Modal` jobs

info: Modal Container File Transfers
    - When using the server's `modal` transcribe backend, the server needs to
      perform network file transfers between the local file system and the
      `Modal` containers which run the GPU processing work

    - These file transfers include either sending an input media file located
      under `HOST_MEDIA_PATH` in the local file system for the container to
      process, or receiving a processed file from the container and saving it
      under `HOST_MEDIA_PATH`

    - Since these files are often large, multi-GB media files, the server
      creates a transient ephemeral `Modal Volume` for every job, which exists
      only for the duration of the job and can be accessed either inside the
      container or locally via a unique identifier

    - For this reason, Jobs receive both the volume's ID and the path in which
      the local runtime saved the input file inside the volume so that the
      container can find that file during the job

info: Modal Volume Lifecycle
    - Before the job starts, the local runtime creates the volume and uploads
      the input media file to it

    - The container then locates the volume via its ID, saves the file to its
      local storage, does any necessary GPU processing, and writes the
      resulting processed file (if any) back to that same volume

    - If there are any resulting processed files, the local runtime then
      accesses the volume again, saves them to the local file system and
      serves it to the user

    - Finally, the job is completed and the ephemeral volume is deleted
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import modal

from ..config import get_settings
from .conversion import video_conversion_job
from .transcription import transcribe_job

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class ModalRuntime:
    """
    Bundle of the ephemeral Modal app and its registered job handles

    Attributes:
        app (modal.App): The fully-configured ephemeral `mirumoji-gpu` app to
            run jobs under
        transcribe (modal.Function): Handle for the transcription job
        convert (modal.Function): Handle for the video-conversion job
    """

    app: modal.App
    transcribe: modal.Function[..., Any, Any]
    convert: modal.Function[..., Any, Any]


def setup_modal() -> ModalRuntime:
    """
    Configures the Mirumoji `Modal` App

    info: `Setup Steps`
        - Defines the pre-built `Docker Image` that the `Modal` container will
          run for every registered function (`MIRUMOJI_MODAL_IMAGE` passed to
          modal's `from_registry`)

        - Creates the ephemeral `mirumoji-gpu` `Modal App` and registers all
          jobs

    Returns:
        A `ModalRuntime` bundling the ephemeral app and its job handles, so
            callers invoke `runtime.transcribe.remote.aio(...)` /
            `runtime.convert.remote.aio(...)` inside `runtime.app.run()`
    """
    settings = get_settings()

    LOGGER.info("Configuring Modal Image")

    # Build Image From Settings
    mirumoji_image = modal.Image.from_registry(
        settings.modal_image,
    )
    app = modal.App("mirumoji-gpu", image=mirumoji_image)

    # Register Jobs
    convert = app.function(
        gpu=settings.modal_gpu,
        timeout=600,
        include_source=True,
    )(video_conversion_job)

    transcribe = app.function(
        gpu=settings.modal_gpu,
        timeout=600,
        include_source=True,
    )(transcribe_job)

    LOGGER.info("Modal Runtime Ready")

    return ModalRuntime(app=app, transcribe=transcribe, convert=convert)
