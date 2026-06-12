"""
Shared `Modal` app and container image used by all `Modal` jobs

warning: Media Paths
    - All `Modal` jobs defined in the `mirumoji-gpu` ephemeral app can only
      process file paths **RELATIVE** to the `HOST_MEDIA_PATH` directory

    - This is because this directory is mounted onto each container running
      the app during startup in order to avoid having to upload files
      independently for each job

    - If an absolute path is provided, the file won't be found in the
      container and the job will fail with a ValueError
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import modal

from ...paths import HOST_MEDIA_PATH
from ..config import get_settings
from .conversion import video_conversion_job
from .transcription import transcribe_job

LOGGER = logging.getLogger("mirumoji")


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
    Configures the Mirumoji `Modal` integration

    info: `Setup Steps`
        - Creates a shared media directory at `HOST_MEDIA_PATH` if it doesn't
          already exist

        - Defines the pre-built `Docker Image` that the `Modal` container will
          run for every registered function

        - Tells `Modal` to mount the shared media directory onto the container
          on every startup in order to make the files available for
          processing during jobs

        - Creates the ephemeral `mirumoji-gpu` `Modal App` and registers all
          jobs

    Returns:
        A `ModalRuntime` bundling the ephemeral app and its job handles, so
            callers invoke `runtime.transcribe.remote.aio(...)` /
            `runtime.convert.remote_gen.aio(...)` inside `runtime.app.run()`
    """
    settings = get_settings()

    # Create Shared Media Directory
    HOST_MEDIA_PATH.mkdir(parents=True, exist_ok=True)
    LOGGER.info(
        f"Modal Setup - Configiguring Image + Mounting '{HOST_MEDIA_PATH}' at "
        f"/root/media_files",
    )

    # Build media_files on modal container startup
    mirumoji_image = modal.Image.from_registry(
        settings.modal_image,
    ).add_local_dir(
        HOST_MEDIA_PATH,
        remote_path="/root/media_files",
    )

    app = modal.App("mirumoji-gpu", image=mirumoji_image)

    # Register Jobs
    convert = app.function(
        gpu=settings.modal_gpu,
        timeout=600,
        include_source=True,
        is_generator=True,
    )(video_conversion_job)

    transcribe = app.function(
        gpu=settings.modal_gpu,
        timeout=600,
        include_source=True,
    )(transcribe_job)

    LOGGER.info("Modal Setup - Ready")

    return ModalRuntime(app=app, transcribe=transcribe, convert=convert)
