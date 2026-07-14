"""
Defines the server's deployed GPU-offload Modal app

The offload backend runs `Whisper` transcription and video conversion on a
`Modal` GPU. This is the server-owned half of the Modal integration (the
launcher owns the full-stack host app). The shared deployment lifecycle lives
in `mirumoji.modal`

question: Why A Deployed Cls
    - An ephemeral app per job (`app.run()`) always spins up a fresh container
      and reloads the multi-GB `Whisper` model

    - A bigger `scaledown_window` can't help because a single job was the only
      call in the app's lifetime

    - `OffloadWorker` is a deployed `modal.Cls` that loads the model once per
      container (`@modal.enter`) and stays warm for `scaledown_window`, so
      back-to-back jobs skip the cold start while `min_containers=0` still lets
      it scale to zero (no idle GPU billing)

info: Auto-Deployed
    The server deploys this app to the user's workspace on first use via
    `ensure_offload_deployed` and tracks it via the `mirumoji.modal` ownership
    tags to ensure that it is never duplicated and is updated in place during
    version upgrades

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
from functools import lru_cache
from typing import Any, Literal

import modal

from ... import __version__
from ...modal import ensure_deployed
from ..config import get_settings

LOGGER = logging.getLogger(__name__)

OFFLOAD_APP_NAME = "mirumoji-offload"
"""
The deployed offload app's name on the user's Modal workspace
"""

WORKER_CLS_NAME = "OffloadWorker"
"""
The offload worker class name, used for `Cls.from_name` lookups
"""


class OffloadWorker:
    """
    Warm GPU worker that transcribes and converts media on `Modal`

    Attributes:
        _model (WhisperModel): The `WhisperModel` loaded once per container at
            entry
    """

    @modal.enter()
    def _load(self) -> None:
        """
        Loads the `Whisper` model once when the container starts

        info: Model Options
            - The model loads once at container entry with the default options

            - `w_transcribe_args` still apply per call


        Runs in the container, so it configures container logging (stdout only,
        captured by Modal as job logs) and builds the model with the default
        options
        """
        from mirumoji.log import setup_logging
        from mirumoji.server.processing import whisper

        setup_logging(log_file=None, console=True)
        logging.getLogger(__name__).info("Loading Whisper Model On Container")
        self._model = whisper.load_model()

    @modal.method()
    def transcribe(
        self,
        vol_fp: str,
        vol_id: str,
        output_format: Literal["srt", "joined"] = "srt",
        *,
        w_transcribe_args: dict[str, Any] | None = None,
    ) -> str:
        """
        Transcribe media on a `Modal` GPU and return raw transcription

        info: Transcription-Only
            - Jobs return raw transcription

            - LLM post-processing (SRT-Fixing) is applied by the `Processor`
              afterwards through the provider-agnostic LLM layer, so the same
              path works for both local and `Modal` transcription

        info: `output_format`
            - When `output_format="srt"`, sentence-level `SRT` content is
              composed from transcription segments, returning a string ready
              to be saved as a `.srt` file

            - When `output_format="joined"`, transcription segment texts are
              joined with the Japanese full stop into a single string without
              any timing information

        info: File Transfer
            - The input media is read out of the per-job ephemeral volume into
              a container-local temp directory before being handed to `Whisper`

            - That directory is removed once the job finishes

        Args:
            vol_fp (str): Path of the input media inside the per-job ephemeral
                volume
            vol_id (str): ID of the per-job ephemeral volume
            output_format (Literal["srt", "joined"]): `srt` for sentence-level
                SRT content, `joined` for a single joined string. Defaults to
                `srt`
            w_transcribe_args (dict | None): Additional arguments for
                `WhisperModel.transcribe`. Overrides the ones set in
                `mirumoji.server.processing.whisper.DEFAULT_TRANSCRIBE_OPTS`

        Returns:
            The raw transcription in the requested format

        Raises:
            ModalVolumeError: If the input can't be read from the volume
            TranscriptionError: If transcription fails
        """
        import logging as _logging
        import shutil
        import tempfile
        from pathlib import Path

        from mirumoji.server.modal_processing.volume_io import (
            download_from_volume,
        )
        from mirumoji.server.processing import whisper

        logger = _logging.getLogger(__name__)
        vol = modal.Volume.from_id(vol_id)
        workdir = Path(tempfile.mkdtemp(prefix="mirumoji_transcribe_"))
        try:
            local_fp = workdir / Path(vol_fp).name
            download_from_volume(vol, vol_fp, local_fp)

            logger.info(
                f"Transcription Started For '{local_fp}' "
                f"(Output Format '{output_format}')"
            )
            segments, _info = whisper.transcribe(
                model=self._model,
                audio_path=local_fp,
                w_transcribe_args=w_transcribe_args,
            )
            logger.info("Transcription Succeeded")

            if output_format == "joined":
                return whisper.to_string(segments)
            return whisper.to_srt(segments)
        finally:
            shutil.rmtree(workdir, ignore_errors=True)

    @modal.method()
    def convert(
        self,
        vol_fp: str,
        vol_id: str,
        to_mp4_kwargs: dict[str, Any] | None = None,
    ) -> str:
        """
        Convert a video to MP4 inside a `Modal` GPU container

        info: Encoder
            - The container probes `NVENC` and uses the on-device GPU pipeline
              only when an encoder is present, falling back to CPU `libx264`
              otherwise

            - The data center compute GPUs (`A100` / `H100` / `B200`)
              have no `NVENC`, so they convert on CPU

        info: File Transfer
            - The input video is read out of the per-job ephemeral volume into
              a container-local temp directory

            - The container converts the video and the resulting MP4 is
              written back into the same volume

            - The job returns the output key so that the local runtime can
              stream the result out and save it

            - The temp directory is removed once the job finishes

        Args:
            vol_fp (str): Path of the input video inside the per-job ephemeral
                volume
            vol_id (str): ID of the per-job ephemeral volume
            to_mp4_kwargs (dict | None): Additional arguments for
                `mirumoji.server.processing.audio.to_mp4`

        Returns:
            The path of the converted MP4 inside the per-job ephemeral volume

        Raises:
            ModalVolumeError: If the input or output can't be transferred
                through the volume
            FFmpegError: If any of the FFMPEG commands return a non-zero exit
                code
            ValueError: If the input doesn't exist or an invalid resolution is
                provided
            MissingFFmpegError: If the FFMPEG executable couldn't be located
            MissingFFprobeError: If the FFPROBE executable couldn't be located
            RuntimeError: If conversion produces no output
        """
        import logging as _logging
        import shutil
        import tempfile
        from pathlib import Path, PurePosixPath

        from mirumoji.server.config import nvenc_available
        from mirumoji.server.modal_processing.volume_io import (
            download_from_volume,
            upload_to_volume,
        )
        from mirumoji.server.processing.audio import get_ffmpeg_path, to_mp4

        logger = _logging.getLogger(__name__)
        vol = modal.Volume.from_id(vol_id)
        workdir = Path(tempfile.mkdtemp(prefix="mirumoji_convert_"))
        try:
            local_in = workdir / Path(vol_fp).name
            download_from_volume(vol, vol_fp, local_in)

            ffmpeg = get_ffmpeg_path()["ffmpeg"]
            use_gpu = nvenc_available(ffmpeg)

            local_out = workdir / f"{local_in.stem}_converted.mp4"
            logger.info(
                f"Converting '{local_in}' -> '{local_out}' "
                f"(use_gpu={use_gpu}, kwargs: {to_mp4_kwargs})"
            )
            kwargs = dict(to_mp4_kwargs or {})
            kwargs.update(
                ffmpeg_path=ffmpeg,
                input_path=local_in,
                output_path=local_out,
                use_gpu=use_gpu,
            )
            result_p = to_mp4(**kwargs)

            if not (
                result_p and result_p.exists() and result_p.stat().st_size > 0
            ):
                raise RuntimeError(
                    f"Video Conversion Failed Or Produced An Empty File "
                    f"For '{local_in}'",
                )

            out_vol_fp = str(PurePosixPath(vol_fp).with_name(local_out.name))
            upload_to_volume(vol, result_p, out_vol_fp)
            logger.info(f"Converted Video Written To '{out_vol_fp}'")
            return out_vol_fp
        finally:
            shutil.rmtree(workdir, ignore_errors=True)


@lru_cache(maxsize=1)
def get_offload_app() -> modal.App:
    """
    Builds the offload app and registers the worker on first use

    info: Import-Safe
        - The app is created here, not at module import, so importing this
          module has no side effects

    info: Container Reconstruction
        - The worker is registered by reference (not `serialized`)

        - `include_source` ships the current source and the deployed container
          rebuilds the worker by re-importing `OffloadWorker` from this module

    Returns:
        The configured `mirumoji-offload` app with `OffloadWorker` registered
    """
    settings = get_settings()
    image = modal.Image.from_registry(settings.modal_image)
    app = modal.App(OFFLOAD_APP_NAME, image=image)
    app.cls(
        gpu=settings.modal_gpu,
        timeout=600,
        scaledown_window=settings.modal_scaledown_window,
        min_containers=0,
        include_source=True,
    )(OffloadWorker)
    return app


def ensure_offload_deployed() -> None:
    """
    Deploys the offload app to the user's workspace unless already current

    Idempotent and tracked through `mirumoji.modal`, so it never duplicates the
    app and rolls it forward when the package version changes

    Raises:
        ModalError: If credentials are missing or the deploy fails
    """
    ensure_deployed(get_offload_app(), OFFLOAD_APP_NAME, version=__version__)


def offload_worker() -> Any:
    """
    Returns a handle to the deployed `OffloadWorker` for remote calls

    The instantiated Modal Cls resolves `.transcribe` / `.convert` through a
    dynamic `__getattr__`, so `Any` is the correct return type

    Returns:
        An `OffloadWorker` instance handle whose `transcribe` / `convert`
            methods expose `.remote.aio(...)` and `.spawn.aio(...)`
    """
    return modal.Cls.from_name(OFFLOAD_APP_NAME, WORKER_CLS_NAME)()
