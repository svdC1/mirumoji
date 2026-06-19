"""
Defines the `Processor` class, the server's stateful transcription/conversion
orchestrator

abstract: Role
    - Routes transcription/conversion to either the `local` backend
      or `Modal`, based on `config.transcribe_backend()`

    - Stateless concerns (tokenization, dictionary lookups, LLM calls) are
      handled directly by their own modules and are intentionally not routed
      through here
"""

from __future__ import annotations

import asyncio
import logging
import os
from collections.abc import AsyncIterator
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, TypeVar, cast

import modal

from ...exceptions import (
    MirumojiServerError,
    ModalError,
    WhisperUnavailableError,
)
from .. import media
from ..config import gpu_available, transcribe_backend
from ..modal_processing import volume_io
from . import audio, whisper

if TYPE_CHECKING:
    from faster_whisper import WhisperModel

    from ..modal_processing.app import ModalRuntime

LOGGER = logging.getLogger(__name__)

K = TypeVar("K")
"""
The id that a caller assigns to one input file in a batch

info: Batch Operations
    - Each input is passed in under this id

    - Its result is yielded back under the same id

    - Results arrive as containers finish (in no fixed order), so this id is
      how the caller tells which input a result belongs to

    - The batch job handlers pass each file's child-job id
"""


class Processor:
    """
    Stateful orchestrator for transcription and video conversion

    Detects the transcription backend on construction and lazily builds the
    required backend dependencies (local `Whisper` model or the `Modal`
    runtime), caching it for reuse

    Attributes:
        backend (str): Resolved transcription backend
            (`local` | `modal` | `none`)
    """

    def __init__(self) -> None:
        self.backend = transcribe_backend()
        self._model: WhisperModel | None = None
        self._runtime: ModalRuntime | None = None
        LOGGER.info(
            f"Processor Initialised (Backend='{self.backend}')",
        )

    # --- Lazy Backends ---

    def _get_model(
        self,
        w_model_args: dict[str, Any] | None = None,
    ) -> WhisperModel:
        """
        Loads the local `WhisperModel` object on first use, returning the
        cached model on subsequent calls

        info: Caching
            The model is built once and cached, so `w_model_args` only
            applies to the first load

        Args:
            w_model_args (dict | None): Additional arguments for
                `WhisperModel`. Overrides the ones set in
                `mirumoji.server.processing.whisper.DEFAULT_MODEL_OPTS`

        Raises:
            WhisperUnavailableError: If `faster-whisper` is not installed or
                the model fails to load

        Returns:
            The local `WhisperModel` object that should be used
        """
        if self._model is None:
            LOGGER.info("Loading Local Whisper Model")
            self._model = whisper.load_model(w_model_args)
        return self._model

    def _get_runtime(self) -> ModalRuntime:
        """
        Configures the `ModelRuntime` bundle on first use, returning the
        cached object on subsequent calls

        Returns:
            The `ModalRuntime` object defining the ephemeral `Modal` app and
                its job handlers
        """
        if self._runtime is None:
            from ..modal_processing.app import setup_modal

            self._runtime = setup_modal()
        return self._runtime

    def _require_transcription(self) -> None:
        """
        Raises if no transcription backend is configured

        Raises:
            WhisperUnavailableError: If the backend resolved to `none`
        """
        if self.backend == "none":
            raise WhisperUnavailableError(
                "No transcription backend is configured. Install the "
                "whisper-local extra or configure Modal",
            )

    # --- Single-File Operations  ---

    async def transcribe(
        self,
        media_path: str | os.PathLike[str],
        output_format: Literal["srt", "joined"] = "srt",
        *,
        w_model_args: dict[str, Any] | None = None,
        w_transcribe_args: dict[str, Any] | None = None,
    ) -> str:
        """
        Transcribes media using either a local `WhisperModel` or the `Modal`
        app's `trancribe_job` function depending on backend configuration

        info: `output_format`
            - When `output_format="srt"`, sentence-level `SRT` content is
              composed from transcription segments, returning a string ready
              to be saved as a `.srt` file

            - When `output_format="joined"`, transcription segment texts are
              joined with the Japanese full stop into a single string without
              any timing information

        info: `w_model_args`
            - When running the `local` backend, the model-loading overrides
              apply only to the first load, since the model used for
              subsequent calls is a cached one

            - When running the `modal` backend, each job runs in an isolated
              container which must rebuild the `WhisperModel` object, so these
              overrides apply for every call

        Args:
            media_path (str | os.PathLike[str]): Absolute path to the media
                within the media directory
            output_format (Literal["srt", "joined"]): `srt` for sentence-level
                SRT content, `joined` for a single joined string. Defaults to
                `srt`
            w_model_args (dict | None): Additional arguments for
                `WhisperModel`. Overrides the ones set in
                `mirumoji.server.processing.whisper.DEFAULT_MODEL_OPTS`
            w_transcribe_args (dict | None): Additional arguments for
                `WhisperModel.transcribe`. Overrides the ones set in
                `mirumoji.server.processing.whisper.DEFAULT_TRANSCRIBE_OPTS`

        Returns:
            The raw transcription in the requested format

        Raises:
            WhisperUnavailableError: If no transcription backend is configured,
                or the local model fails to load
            TranscriptionError: If transcription fails (raised locally, or
                propagated unchanged from the Modal job when preserved)
            InvalidMediaPathError: If the media path is outside the media
                directory (Modal backend)
            ModalError: If the Modal job fails for any other reason
        """
        self._require_transcription()
        LOGGER.info(
            f"Transcribing '{media_path}' Via '{self.backend}' Backend "
            f"(Format '{output_format}')"
        )
        if self.backend == "modal":
            # Stream the input into a per-job ephemeral volume
            # (the only surface shared with the container), keyed by its
            # media-relative path
            runtime = self._get_runtime()
            src = Path(media_path)
            vol_fp = media.get_relative_path(media_path).as_posix()
            try:
                # Create Ephemeral Volume
                async with modal.Volume.ephemeral() as vol:
                    # Upload File
                    await asyncio.to_thread(
                        volume_io.upload_to_volume,
                        vol,
                        src,
                        vol_fp,
                    )
                    # Run Transcription
                    async with runtime.app.run():
                        result = await runtime.transcribe.remote.aio(
                            vol_fp=vol_fp,
                            vol_id=vol.object_id,
                            output_format=output_format,
                            w_model_args=w_model_args,
                            w_transcribe_args=w_transcribe_args,
                        )
                return cast(str, result)
            except MirumojiServerError:
                # Domain exceptions are preserved across the Modal boundary
                raise
            except Exception as e:
                raise ModalError(
                    f"Modal Transcription Job Failed: {e}",
                ) from e

        # Local Backend
        model = self._get_model(w_model_args)
        segments, _info = await asyncio.to_thread(
            whisper.transcribe,
            model=model,
            audio_path=media_path,
            w_transcribe_args=w_transcribe_args,
        )
        if output_format == "joined":
            return whisper.to_string(segments)
        return whisper.to_srt(segments)

    async def convert_to_mp4(
        self,
        input_path: str | os.PathLike[str],
        output_path: str | os.PathLike[str],
        to_mp4_kwargs: dict[str, Any] | None = None,
    ) -> Path:
        """
        Converts a video to MP4 using `FFMPEG`

        info: Backend Differences
            - When using the `local` backend, an attempt is made to use the
              local NVIDIA GPU's `NVENC` for faster encoding. If this a CPU
              deployment or `NVENC` fails for any reason, it falls back to the
              slower CPU enconding

            - When using the `modal` backend, the conversion happens inside a
              `Modal` container running a image that is already configured
              with `NVENC` capability, so `NVENC` enconding is used

        Args:
            input_path (str | os.PathLike[str]): Absolute path to the source
                video
            output_path (str | os.PathLike[str]): Absolute destination path for
                the MP4
            to_mp4_kwargs (dict | None): Argument overrides for `audio.to_mp4`
                (resolution, target_bitrate, use_gpu)

        Returns:
            The path to the converted MP4

        Raises:
            MissingFFmpegError: If the FFMPEG executable can't be located
                (local backend)
            MissingFFprobeError: If the FFPROBE executable can't be located
                (local backend)
            FFmpegError: If an FFMPEG command fails (local or modal backend)
            ValueError: If the source isn't a valid file or the resolution is
                malformed (local or modal backend)
            InvalidMediaPathError: If the source path is outside the media
                directory (Modal backend)
            ModalError: If the Modal conversion job fails
        """
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        LOGGER.info(
            f"Converting '{input_path}' To MP4 Via '{self.backend}' Backend"
        )

        if self.backend == "modal":
            # Stream the source into a per-job ephemeral volume,
            # convert on the GPU container which writes the MP4 back into the
            # same volume, then stream the result back out into `out`
            runtime = self._get_runtime()
            src = Path(input_path)
            vol_fp = media.get_relative_path(input_path).as_posix()
            try:
                # Create Volume
                async with modal.Volume.ephemeral() as vol:
                    # Upload File
                    await asyncio.to_thread(
                        volume_io.upload_to_volume,
                        vol,
                        src,
                        vol_fp,
                    )
                    # Run Conversion
                    async with runtime.app.run():
                        out_vol_fp = await runtime.convert.remote.aio(
                            vol_fp=vol_fp,
                            vol_id=vol.object_id,
                            to_mp4_kwargs=to_mp4_kwargs,
                        )
                    # Save Converted File Back To Local Storage
                    await asyncio.to_thread(
                        volume_io.download_from_volume,
                        vol,
                        cast(str, out_vol_fp),
                        out,
                    )
            except MirumojiServerError:
                # Domain Exceptions are preserved across the Modal boundary
                raise
            except Exception as e:
                raise ModalError(
                    f"Modal Video Conversion Job Failed: {e}",
                ) from e
            return out

        # Local Backend. Only attempt the GPU path when a CUDA device is
        # actually present, so CPU-only deployments don't waste a doomed NVENC
        # attempt before falling back
        kwargs = {
            "use_gpu": bool(gpu_available()["available"]),
            **(to_mp4_kwargs or {}),
        }
        await asyncio.to_thread(
            audio.to_mp4,
            ffmpeg_path=audio.get_ffmpeg_path()["ffmpeg"],
            input_path=str(input_path),
            output_path=str(out),
            **kwargs,
        )
        return out

    # --- Modal Batch Helpers ---

    @staticmethod
    async def _upload_inputs(
        vol: modal.Volume,
        sources: dict[K, Path],
    ) -> dict[K, str]:
        """
        Streams every batch input into a shared Modal volume under a unique
        path

        Each in-volume path is namespaced by the input's id so that two inputs
        with the same file name never collide in the volume

        Args:
            vol (modal.Volume): The shared ephemeral batch volume
            sources (dict[K, Path]): Each input's local file, mapped from its
                id

        Returns:
            Each input's in-volume path, under the same ids as `sources`
        """
        vol_fps: dict[K, str] = {}
        for key, src in sources.items():
            vol_fp = f"batch/{key}/{Path(src).name}"
            await asyncio.to_thread(
                volume_io.upload_to_volume,
                vol,
                Path(src),
                vol_fp,
            )
            vol_fps[key] = vol_fp
        return vol_fps

    @staticmethod
    async def _collect_transcribe(
        key: K,
        call: modal.FunctionCall[str],
    ) -> tuple[K, str | MirumojiServerError]:
        """
        Awaits one batched Modal transcription call, tagging it with its input
        id

        Args:
            key (K): The id of the input that produced this call
            call (modal.FunctionCall): The spawned transcription call handle

        Returns:
            The id paired with its raw transcription, or with the input's
                failure (domain exceptions preserved, others wrapped in
                `ModalError`)
        """
        try:
            result = await call.get.aio()
            return key, result
        except MirumojiServerError as exc:
            return key, exc
        except Exception as exc:
            return key, ModalError(f"Modal Transcription Job Failed: {exc}")

    @staticmethod
    async def _collect_convert(
        key: K,
        call: modal.FunctionCall[str],
        vol: modal.Volume,
        out_path: Path,
    ) -> tuple[K, Path | MirumojiServerError]:
        """
        Awaits one batched Modal conversion call and streams its MP4 out
        locally

        Args:
            key (K): The id of the input that produced this call
            call (modal.FunctionCall): The spawned conversion call handle
            vol (modal.Volume): The shared batch volume holding the output
            out_path (Path): Local destination for the converted MP4

        Returns:
            The id paired with the converted MP4's local path, or with the
                input's failure (domain exceptions preserved, others wrapped in
                `ModalError`)
        """
        try:
            out_vol_fp = await call.get.aio()
            await asyncio.to_thread(
                volume_io.download_from_volume,
                vol,
                out_vol_fp,
                out_path,
            )
            return key, out_path
        except MirumojiServerError as exc:
            return key, exc
        except Exception as exc:
            return key, ModalError(f"Modal Video Conversion Job Failed: {exc}")

    # --- Batch Operations ---

    async def transcribe_batch(
        self,
        sources: dict[K, Path],
        output_format: Literal["srt", "joined"] = "srt",
        *,
        w_model_args: dict[str, Any] | None = None,
        w_transcribe_args: dict[str, Any] | None = None,
    ) -> AsyncIterator[tuple[K, str | MirumojiServerError]]:
        """
        Transcribes many already-prepared audio files on `Modal` in parallel

        info: Modal-Only
            - This is the `modal` backend's batch fan-out path and assumes the
              backend resolved to `modal`

            - The `local` backend has a single GPU, so its batches run the
              per-file transcription sequentially instead of calling this

        info: Fan-Out
            - All inputs share one ephemeral volume and one app run, then each
              file is `spawn`-ed to its own container, bounded by the account's
              concurrent-GPU limit

            - Results are yielded as each container finishes (in no fixed
              order), so the caller can update per-file state live

        info: Result Keys
            - `sources` maps each input's id to its audio file, and each result
              is yielded under that same id

            - Because results arrive out of order, the id is how the caller
              knows which input a result belongs to

            - In practice it is the file's child-job id, so the handler writes
              the result straight onto the matching child row

        info: Per-File Isolation
            - One file failing does not fail the batch

            - A failed file yields its exception instead of raising, so
              sibling files still complete

            - Domain exceptions are preserved across the Modal boundary, other
              failures are wrapped in `ModalError`

        Args:
            sources (dict[K, Path]): Each input's local prepared audio file,
                mapped from the id the caller assigned to that input
            output_format (Literal["srt", "joined"]): `srt` for sentence-level
                SRT content, `joined` for a single joined string
            w_model_args (dict | None): Additional arguments for `WhisperModel`
            w_transcribe_args (dict | None): Additional arguments for
                `WhisperModel.transcribe`

        Yields:
            `(id, result)` for each input as its container finishes, where `id`
                is the one the input was passed in under and `result` is the
                raw transcription or that input's failure
        """
        runtime = self._get_runtime()
        async with modal.Volume.ephemeral() as vol:
            vol_fps = await self._upload_inputs(vol, sources)

            async with runtime.app.run():
                pending = []
                for key, vol_fp in vol_fps.items():
                    call = await runtime.transcribe.spawn.aio(
                        vol_fp=vol_fp,
                        vol_id=vol.object_id,
                        output_format=output_format,
                        w_model_args=w_model_args,
                        w_transcribe_args=w_transcribe_args,
                    )
                    pending.append(self._collect_transcribe(key, call))

                for finished in asyncio.as_completed(pending):
                    yield await finished

    async def convert_batch(
        self,
        sources: dict[K, Path],
        out_paths: dict[K, Path],
        *,
        to_mp4_kwargs: dict[str, Any] | None = None,
    ) -> AsyncIterator[tuple[K, Path | MirumojiServerError]]:
        """
        Converts many videos to MP4 on `Modal` in parallel

        info: Modal-Only
            - This is the `modal` backend's batch fan-out path and assumes the
              backend resolved to `modal`

            - The `local` backend converts its batches one file at a time
              instead of calling this

        info: Fan-Out
            - All inputs share one ephemeral volume and one app run, each file
              is `spawn`-ed to its own GPU container

            - Each converted MP4 is streamed back out to its local destination
              as the file finishes

        info: Result Keys
            - `sources` and `out_paths` map each input's id to its source video
              and its destination, and each result is yielded under that same
              id

            - Because results arrive out of order, the id is how the caller
              knows which input a result belongs to

            - In practice it is the file's child-job id

        info: Per-File Isolation
            - One file failing yields its exception instead of raising, so
              sibling files still complete

            - Domain exceptions are preserved, other failures are wrapped in
              `ModalError`

        Args:
            sources (dict[K, Path]): Each input's local source video, mapped
                from the id the caller assigned to that input
            out_paths (dict[K, Path]): Each input's local MP4 destination,
                under the same ids as `sources`
            to_mp4_kwargs (dict | None): Argument overrides for `audio.to_mp4`

        Yields:
            `(id, result)` for each input as its container finishes, where `id`
                is the one the input was passed in under and `result` is the
                converted MP4's local path or that input's failure
        """
        runtime = self._get_runtime()
        async with modal.Volume.ephemeral() as vol:
            vol_fps = await self._upload_inputs(vol, sources)

            async with runtime.app.run():
                pending = []
                for key, vol_fp in vol_fps.items():
                    call = await runtime.convert.spawn.aio(
                        vol_fp=vol_fp,
                        vol_id=vol.object_id,
                        to_mp4_kwargs=to_mp4_kwargs,
                    )
                    pending.append(
                        self._collect_convert(key, call, vol, out_paths[key]),
                    )

                for finished in asyncio.as_completed(pending):
                    yield await finished
