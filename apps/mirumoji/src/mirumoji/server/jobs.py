"""
Defines classes and functions to manage the server's asynchronous job queue,
which handles the execution of long-running operations

info: Long-Running Operations
    - Transcription
    - SRT Generation
    - Media Conversion
    - LLM SRT-Fixing

info: How It Works
    - Jobs are queued in-process and run by a single worker coroutine
      that is initialised on app startup and persists throughout its
      lifecycle

    - Each job references an `existing` profile file and persists its
      output back as profile files or transcripts, which is what lets the
      client operate on server-side media without re-uploading it
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import time
import uuid
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, TypeAlias

from ..exceptions import MirumojiServerError, RecordNotFoundError
from . import media
from .config import get_settings
from .db import UnitOfWork
from .models.requests import (
    ConvertVideoRequest,
    GenerateSrtRequest,
    TranscribeAudioRequest,
)
from .models.responses import (
    BatchResult,
    ConvertResult,
    JobResult,
    SrtResult,
    TranscribeResult,
)
from .processing import audio, llm
from .processing.subtitles import sanitize_srt

if TYPE_CHECKING:
    from .db.models import FileDTO, JobDTO
    from .processing.processor import Processor

    _JobHandler: TypeAlias = Callable[
        [JobDTO, Processor],
        Awaitable[JobResult],
    ]
    """
    The signature of a `Job Handler Function`

    A Job Handler function runs the operation for a job and returns its
    results (e.g File references, strings, ...) in an awaitable coroutine
    """

    _PerFileCore: TypeAlias = Callable[
        [str, dict[str, Any], Processor],
        Awaitable[JobResult],
    ]
    """
    The signature of a `Per-File Core Function`

    A Per-File Core function runs one operation using a single file given a
    profile id and a single-op `params` mapping, returning its result. It
    carries no job bookkeeping, so it is shared by a single-op handler and by
    a local batch runner that calls it once per child
    """

LOGGER = logging.getLogger(__name__)


# --- Manager ---


class JobQueueManager:
    """
    abstract: Usage
        Allows the client to submit long-running operation requests and tracks
        their statuses across navigation through the `jobs` database table

    info: Durability
        - The queue is in-process and does not survive a restart

        - On shutdown, `stop` attempts to fail any job still left running

       - On startup, `start` fails any job still left `running` because of a
         server crash and re-queues any `queued` job

    info: Concurrency
        - One worker runs jobs sequentially, so 2 or more heavy, local GPU/CPU
          operations never run simultaneously

        - Cross-file parallelism for batches is the job handler's concern,
          not the worker's

    info: Job Handlers
        - A `Job Handler` is a function that runs an operation for a job
          with a specific `type` attribute and returns its results (e.g File
          references, strings, ...) in an awaitable coroutine

        - Handlers are keyed by the job `type` that they execute in an
          instace-scoped dictionary

        - Handlers can be registered to an instance by using the
          `register_handler` method, which accepts both the handler function
          and a string representing the specific job `type` which the handler
          executes

        - The `_run_job` function queries the database for the provided `job_id
          , looks up its `type` attribute and routes execution to the
          designated registered handling, failing jobs whose `type` doesn't
          match any registered handler

    Attributes:
        queue (asyncio.Queue[uuid.UUID] | None): The in-process job queue,
            created in `start` once the loop is running

        _worker_task (asyncio.Task[None] | None): The running worker coroutine
            , or `None` when the worker is stopped

        processor (Processor): The running app's lifecycle-scoped `Processor`
            instance which orchestrates actual job execution and is passed to
            `Job Handler` functions

        handlers (dict[str, _JobHandler]): A dictionary mapping registered
            `_JobHandler` functions to the job `type` that they execute
    """

    def __init__(self, processor: Processor) -> None:
        # Only initialise queue at startup
        self.queue: asyncio.Queue[uuid.UUID] | None = None
        self._worker_task: asyncio.Task[None] | None = None
        self.processor = processor
        self.handlers: dict[str, _JobHandler] = {}
        # The job the worker is currently executing, so its row is never
        # deleted out from under it (a `cancelled` job may still be in flight)
        self._running: uuid.UUID | None = None

    @property
    def running_job_id(self) -> uuid.UUID | None:
        """
        The id of the job the worker is currently executing, or `None`

        Returns:
            The in-flight job id, or `None` when the worker is idle
        """
        return self._running

    def _ensure_queue(self) -> asyncio.Queue[uuid.UUID]:
        """
        Returns the running queue, raising if it hasn't been started yet

        Returns:
            The instance's job queue, created by `start`

        Raises:
            RuntimeError: If the instance's queue hasn't been initialised with
                `start` before the call
        """
        if self.queue is None:
            raise RuntimeError(
                "Async Queue Is Not Running, Can't Proceed With Worker "
                "Operation",
            )
        return self.queue

    async def _terminate_job(
        self,
        job_id: uuid.UUID,
        *,
        total: int = 1,
        result: JobResult | None = None,
        error: str | None = None,
        error_code: str | None = None,
        error_details: dict[str, Any] | None = None,
    ) -> None:
        """
        Persists a job's terminal state to the database

        info: Cancellation
            - A cancellation request can land while the job runs

            - If the job is already `cancelled` by the time it finishes, that
              status is honored over `succeeded`

            - Any produced `result` is still recorded so that the client can
              inspect what finished before the cancellation

        info: Deletion
            - The job may be deleted while it runs, so a missing row is
              tolerated and the call returns quietly rather than erroring

        info: Work Items
            - On success, `completed` is set to `total`

            - That value is `1` for a single job and `N` for a batch parent,
              so a finished batch reports every file as done

        Args:
            job_id (uuid.UUID): The id of the job to terminate
            total (int): The job's work-item count (`1` for a single job, `N`
                for a batch parent)
            result (JobResult | None): The job's successful result
            error (str | None): The message returned by the job on failure
            error_code (str | None): The stable error code on failure
            error_details (dict | None): Structured error context on failure
        """
        async with UnitOfWork() as uow:
            try:
                current = await uow.jobs.get(job_id)
                if current.status == "cancelled":
                    if result is not None:
                        await uow.jobs.update(
                            job_id, result=result.model_dump()
                        )
                        await uow.commit()
                    return
                if error is not None:
                    await uow.jobs.update(
                        job_id,
                        status="failed",
                        error=error,
                        error_code=error_code,
                        error_details=error_details,
                    )
                else:
                    await uow.jobs.update(
                        job_id,
                        status="succeeded",
                        progress=1.0,
                        completed=total,
                        result=result.model_dump() if result else {},
                    )
                await uow.commit()
            except RecordNotFoundError:
                # The job was deleted while it ran -> nothing to terminate
                return

    async def _run_job(self, job_id: uuid.UUID) -> None:
        """
        Runs a single job, transitioning it through `running` to `succeeded` or
        `failed` and recording its result or error to the database

        Uses the instance's `handlers` dictionary to route job
        execution to a registered `_JobHandler` function based on the
        job's `type` attribute

        If a job has a `type` attribute which does not have a key in the
        `handlers` dictionary, and therefore no designated handler, it is
        intantly marked as failed with the error `Unknown Job Type`

        Args:
            job_id (uuid.UUID): The id of the job to run

        Raises:
            RuntimeError: If the instance's queue hasn't been initialised with
                `start` before the call
        """
        self._ensure_queue()
        # Mark the worker as holding this job, so its row can't be deleted out
        # from under the bookkeeping below (cleared however the job ends)
        self._running = job_id
        try:
            # Skip A Job Cancelled (Or Deleted) While Queued, Otherwise Mark It
            # Running. The `cancel` endpoint can only mark the job "cancelled"
            # in the DB, but by then the job's id is already sitting in the
            # in-process asyncio.Queue, and you can't pull a specific item back
            # out of a Queue, so skip it here instead to honor the DB status
            async with UnitOfWork() as uow:
                try:
                    job = await uow.jobs.get(job_id)
                except RecordNotFoundError:
                    return
                if job.status == "cancelled":
                    return
                job = await uow.jobs.update(job_id, status="running")
                await uow.commit()

            LOGGER.info(
                f"Job '{job_id}' ('{job.type}') Started "
                f"For Profile '{job.profile_id}'"
            )
            started_at = time.monotonic()

            handler = self.handlers.get(job.type)

            if handler is None:
                # Fail The Job If It Has No Registered Handler
                await self._terminate_job(
                    job_id,
                    error=f"Unknown Job Type '{job.type}'",
                )
                return

            try:
                result = await handler(job, self.processor)
            except MirumojiServerError as exc:
                # Domain Failure -> Surface the stable code + the message
                LOGGER.warning(
                    f"Job '{job_id}' ({job.type}) Failed: {exc.code}"
                )
                await self._terminate_job(
                    job_id,
                    error=str(exc),
                    error_code=exc.code,
                    error_details=exc.details,
                )
                # A batch that fails at the orchestration level leaves children
                # mid-flight, so fail them too (a no-op for a single job)
                await _fail_orphaned_children(job_id)
                return
            except Exception:
                # Unexpected Failure -> Log it, but don't leak the raw message
                LOGGER.exception(f"Job '{job_id}' ({job.type}) Failed")
                await self._terminate_job(
                    job_id,
                    error="An Unexpected Error Occurred",
                    error_code="ServerError",
                )
                await _fail_orphaned_children(job_id)
                return

            # Job Succeeded
            await self._terminate_job(job_id, total=job.total, result=result)
            LOGGER.info(
                f"Job '{job_id}' ('{job.type}') Succeeded In "
                f"{time.monotonic() - started_at:.1f}s"
            )
        finally:
            self._running = None

    async def _worker_loop(self) -> None:
        """
        Continuously runs queued jobs one at a time until cancelled with `stop`

        Raises:
            RuntimeError: If the instance's queue hasn't been initialised with
                `start` before the call
        """
        queue = self._ensure_queue()

        while True:
            job_id = await queue.get()

            try:
                await self._run_job(job_id)
            except Exception:
                LOGGER.exception(f"Worker Crashed Running Job '{job_id}'")
            finally:
                queue.task_done()

    async def submit_job(
        self,
        job_id: uuid.UUID,
    ) -> None:
        """
        Adds an already persisted job to the queue for the worker to run

        Args:
            job_id (uuid.UUID): The id of the job to enqueue

        Raises:
            RuntimeError: If the instance's queue hasn't been initialised with
                `start` before the call
        """
        queue = self._ensure_queue()
        await queue.put(job_id)

    async def _rebuild_queue(self) -> None:
        """
        Rebuilds the asynchronous queue on server restarts from the jobs
        presisted in the database on previous runs, requeuing any `queued` jobs

        info: Server Crashes
            Like `stop`, this function also marks jobs with `running` status
            as `failed` in the case that the server happened to crash on a
            previous run without being able to do so

        info: Batches
            - Only top-level jobs are re-queued

            - A re-queued batch parent re-runs and reprocesses its own
              still-`queued` children, so those children are left untouched
              rather than re-queued as standalone single ops

            - A child whose parent is not being re-queued (its batch was
              interrupted mid-run) is orphaned, so it is failed alongside the
              running jobs

        Raises:
            RuntimeError: If the instance's queue hasn't been initialised with
                `start` before the call
        """
        self._ensure_queue()
        async with UnitOfWork() as uow:
            unfinished = await uow.jobs.list_unfinished()
            # Batch parents that will re-run and reprocess their own children
            requeued_parents = {
                job.id
                for job in unfinished
                if job.parent_id is None and job.status == "queued"
            }
            requeue: list[uuid.UUID] = []
            orphaned = 0
            for job in unfinished:
                if job.status == "running":
                    await uow.jobs.update(
                        job.id,
                        status="failed",
                        error="Interrupted By A Server Restart",
                    )
                    orphaned += 1
                elif job.parent_id is None:
                    # A top-level queued job re-runs from the queue
                    requeue.append(job.id)
                elif job.parent_id in requeued_parents:
                    # A queued child whose batch re-runs is left for the parent
                    continue
                else:
                    # A queued child orphaned by an interrupted batch
                    await uow.jobs.update(
                        job.id,
                        status="failed",
                        error="Interrupted By A Server Restart",
                    )
                    orphaned += 1
            await uow.commit()

            for job_id in requeue:
                await self.submit_job(job_id)

        if orphaned:
            LOGGER.warning(
                f"Failed {orphaned} Orphaned Running "
                f"Job(s) From A Previous Run"
            )
        LOGGER.info(f"Re-Queued {len(requeue)} Job(s)")

    async def start(self) -> None:
        """
        Starts the worker and rebuilds the asynchronous queue on server
        restarts from the jobs presisted in the database on previous runs,
        requeuing any `queued` jobs
        """

        self.queue = asyncio.Queue()
        LOGGER.info("Job Worker Started")
        await self._rebuild_queue()

        self._worker_task = asyncio.create_task(self._worker_loop())

    async def stop(self) -> None:
        """
        Stops the worker coroutine, cancelling any in-flight wait and marking
        running jobs as failed
        """

        if self._worker_task is not None:
            # Mark Any Running Job As Failed
            async with UnitOfWork() as uow:
                unfinished = await uow.jobs.list_unfinished()
                interrupted = 0
                for job in unfinished:
                    if job.status == "running":
                        await uow.jobs.update(
                            job.id,
                            status="failed",
                            error="Interrupted By A Server Restart",
                        )
                        interrupted += 1
                await uow.commit()
            if interrupted:
                LOGGER.warning(
                    f"Marked {interrupted} Running Job(s) Failed On Shutdown"
                )
            self._worker_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._worker_task
            self._worker_task = None

            # Cancelling the worker leaves any FFMPEG subprocess it was running
            # alive in a detached thread, since a thread cannot be interrupted.
            # Terminate it so an in-flight conversion does not outlive the
            # server and keep the media file (and process) alive
            await asyncio.to_thread(audio.terminate_running_commands)

        self.queue = None

        LOGGER.info("Job Worker Stopped")

    def register_handler(self, job_type: str, handler: _JobHandler) -> None:
        """
        Register a new `Job Handler` to the instance

        Args:
            job_type (str): The `type` attribute of the jobs that this handler
                is supposed to execute

            handler (_JobHandler): The `JobHandler` function that executes
                this `type` of job
        """
        self.handlers[job_type] = handler


# --- Helpers ---


async def _clean_temp(temp_dir: Path) -> None:
    """
    Performs a best-effort attempt to delete a temporary directory inside
    `HOST_MEDIA_PATH`, logging an exception in case of failures

    Args:
        temp_dir (Path): The path of the directory to delete, relative to
            `HOST_MEDIA_PATH`
    """
    try:
        await media.delete_dir(media.get_relative_path(temp_dir))
    except Exception:
        LOGGER.warning(f"Failed To Clean Temp Dir '{temp_dir}'", exc_info=True)


async def _file_path(file_id: uuid.UUID) -> Path:
    """
    Resolves a profile file's absolute path from its id by attaching
    `HOST_MEDIA_PATH` to it

    Args:
        file_id (uuid.UUID): The profile file id

    Returns:
        The file's absolute path under the media root
    """
    async with UnitOfWork() as uow:
        file_rec = await uow.files.get(file_id)
    return media.BASE_PATH / file_rec.path


# Subtitle files come from anywhere, so they are not always UTF-8 (Shift-JIS is
# common for Japanese subtitles). Try the likely encodings in order
_TEXT_ENCODINGS = ("utf-8-sig", "utf-8", "cp932")


def _read_text_best_effort(path: Path) -> str:
    """
    Reads a subtitle file, tolerating the common non-UTF-8 encodings

    Tries UTF-8 (with and without a BOM) then Shift-JIS. A file that decodes as
    none of these is not usable subtitle text, so the final attempt's
    `UnicodeDecodeError` is allowed to surface and fail the job loudly

    Args:
        path (Path): The file to read

    Returns:
        The decoded text

    Raises:
        UnicodeDecodeError: If the file is not text in any expected encoding
    """
    data = path.read_bytes()
    *fallbacks, final = _TEXT_ENCODINGS
    for encoding in fallbacks:
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode(final)


# --- Per-File Helpers ---


async def _extract_audio(src: Path) -> tuple[Path, Path]:
    """
    Extracts an audio track from a media file and saves it to a new temp
    directory under the `HOST_MEDIA_PATH` directory

    Args:
        src (Path): Absolute path to the source media

    Returns:
        The extracted audio path and the temp directory holding it, which the
            caller cleans once the audio is no longer needed
    """
    op_id = uuid.uuid4().hex
    tmp = media.get_temp_dir(op_id)
    ffmpeg = audio.get_ffmpeg_path()["ffmpeg"]
    extracted = await asyncio.to_thread(
        audio.extract_audio,
        ffmpeg,
        str(src),
        str(tmp / f"{op_id}.wav"),
    )
    return Path(extracted), tmp


async def _filter_audio(
    src: Path,
    *,
    clean: bool,
) -> tuple[Path, Path | None]:
    """
    Cleans an audio track using `media.filter_audio` when `clean` is `True`.
    Otherwise returns the source path unchanged

    Args:
        src (Path): Absolute path to the source media
        clean (bool): Apply a band-pass + loudness filter before transcribing

    Returns:
        The audio path to transcribe and the temp directory holding it, or a
            tuple containing `src` and `None`
    """
    if not clean:
        return src, None
    op_id = uuid.uuid4().hex
    tmp = media.get_temp_dir(op_id)
    ffmpeg = audio.get_ffmpeg_path()["ffmpeg"]
    cleaned = tmp / f"cleaned_{op_id}.wav"
    await asyncio.to_thread(
        audio.filter_audio,
        ffmpeg,
        str(src),
        str(cleaned),
    )
    return cleaned, tmp


def _derived_srt_name(source_name: str, origin: str) -> str:
    """
    Builds a readable SRT display name from its source file's name

    info: SRT File Names
        - A generated SRT takes the source's stem (`ep1.mkv` -> `ep1.srt`)

        - A fixed SRT appends a marker (`ep1.srt` -> `ep1 (fixed).srt`),
          stripping an existing marker first so re-fixing never stacks it

    Args:
        source_name (str): The input file's display name
        origin (str): `generated` or `fixed`

    Returns:
        The derived SRT display name
    """
    stem = Path(source_name).stem.removesuffix(" (fixed)")
    return f"{stem} (fixed).srt" if origin == "fixed" else f"{stem}.srt"


async def _persist_srt(
    profile_id: str,
    content: str,
    *,
    source: FileDTO,
    origin: str,
) -> SrtResult:
    """
    Writes a `.SRT` from `content` in a profile's subtitle directory,
    persisting the file reference linked to its source media

    The storage `path` stays op-id based (traversal-safe); the display `name`,
    `folder`, and root `source_file_id` are inherited from `source` so the SRT
    is readable and grouped under its video

    Args:
        profile_id (str): Owning profile id
        content (str): The SRT content to store
        source (FileDTO): The input file (the source video for a generated SRT,
            or the SRT being fixed), used to derive the name, folder, and the
            root source lineage
        origin (str): `generated` or `fixed`

    Returns:
        The new SRT file's id, media URL, and content
    """
    op_id = uuid.uuid4().hex
    srt_loc = media.get_profile_dir(profile_id, "subtitles") / f"{op_id}.srt"
    rel_srt = media.get_relative_path(srt_loc)
    await media.write_file(rel_srt, content)
    async with UnitOfWork() as uow:
        rec = await uow.files.add(
            profile_id=profile_id,
            name=_derived_srt_name(source.name, origin),
            path=str(rel_srt),
            type="srt",
            folder=source.folder,
            source_file_id=source.source_file_id or source.id,
            origin=origin,
        )
        await uow.commit()
    return SrtResult(
        srt_file_id=str(rec.id),
        srt_url=f"/media/{rel_srt.as_posix()}",
        srt_content=content,
    )


async def _persist_transcript(
    profile_id: str,
    file_id: uuid.UUID,
    text: str,
) -> TranscribeResult:
    """
    Persists a transcript (`file_id`) to a profile's transcripts folder and
    writes it into the database

    Args:
        profile_id (str): Owning profile id
        file_id (uuid.UUID): The source file id
        text (str): The transcription text

    Returns:
        The new transcript's id and text
    """
    async with UnitOfWork() as uow:
        rec = await uow.transcripts.add(
            profile_id=profile_id,
            file_id=file_id,
            text=text,
        )
        await uow.commit()
    return TranscribeResult(transcript_id=str(rec.id), transcript=text)


def _converted_out_path(profile_id: str, source_name: str) -> Path:
    """
    Builds the destination path for a converted MP4

    The output is named after the original upload rather than its op-id storage
    path, so that the client sees a recognisable file name

    Args:
        profile_id (str): Owning profile id
        source_name (str): The source file's display name

    Returns:
        The absolute destination path under the profile's converted folder
    """
    op_id = uuid.uuid4().hex
    return media.get_profile_dir(profile_id, "converted") / (
        f"{Path(source_name).stem}_{op_id}_converted.mp4"
    )


async def _persist_converted(
    profile_id: str,
    rel_out: Path,
    *,
    source: FileDTO,
) -> ConvertResult:
    """
    Persists an already-written converted MP4 as a profile file linked to its
    source video

    The display `name`, `folder`, and root `source_file_id` are inherited from
    `source` so the MP4 is readable and grouped under its video

    Args:
        profile_id (str): Owning profile id
        rel_out (Path): The MP4's media-relative path
        source (FileDTO): The source video, used to derive the name, folder,
            and the root source lineage

    Returns:
        The new MP4 file's id and media URL
    """
    async with UnitOfWork() as uow:
        rec = await uow.files.add(
            profile_id=profile_id,
            name=f"{Path(source.name).stem}.mp4",
            path=str(rel_out),
            type="mp4",
            folder=source.folder,
            source_file_id=source.source_file_id or source.id,
            origin="converted",
        )
        await uow.commit()
    return ConvertResult(
        file_id=str(rec.id),
        video_url=f"/media/{rel_out.as_posix()}",
    )


# --- Per-File Cores ---


async def _generate_srt(
    profile_id: str,
    params: dict[str, Any],
    processor: Processor,
) -> SrtResult:
    """
    Generates raw SRT from one profile video/audio file and stores it

    Args:
        profile_id (str): Owning profile id
        params (dict): Single-op params holding a `file_id` and an optional
            `GenerateSrtRequest`-shaped `opts`
        processor (Processor): The transcription orchestrator

    Returns:
        The new SRT file's id, media URL, and content
    """
    async with UnitOfWork() as uow:
        source = await uow.files.get(uuid.UUID(params["file_id"]))
    src = media.BASE_PATH / source.path
    opts = GenerateSrtRequest.model_validate(params.get("opts") or {})
    audio_path, tmp = await _extract_audio(src)
    try:
        srt_content = await processor.transcribe(
            audio_path,
            output_format="srt",
            w_transcribe_args=opts.model_dump(exclude_none=True),
        )
        return await _persist_srt(
            profile_id, srt_content, source=source, origin="generated"
        )
    finally:
        await _clean_temp(tmp)


async def _transcribe(
    profile_id: str,
    params: dict[str, Any],
    processor: Processor,
) -> TranscribeResult:
    """
    Transcribes one profile audio file to joined text and stores a transcript

    Args:
        profile_id (str): Owning profile id
        params (dict): Single-op params holding a `file_id` and an optional
            `TranscribeAudioRequest`-shaped `opts`
        processor (Processor): The transcription orchestrator

    Returns:
        The new transcript's id and text
    """
    file_id = uuid.UUID(params["file_id"])
    src = await _file_path(file_id)
    opts = TranscribeAudioRequest.model_validate(params.get("opts") or {})
    w_transcribe_args = opts.model_dump(
        exclude_none=True,
        exclude={"clean_audio"},
    )
    source, tmp = await _filter_audio(src, clean=opts.clean_audio)
    try:
        text = await processor.transcribe(
            source,
            output_format="joined",
            w_transcribe_args=w_transcribe_args,
        )
        return await _persist_transcript(profile_id, file_id, text)
    finally:
        if tmp is not None:
            await _clean_temp(tmp)


async def _convert(
    profile_id: str,
    params: dict[str, Any],
    processor: Processor,
) -> ConvertResult:
    """
    Converts one profile video file to MP4 and stores the result

    Args:
        profile_id (str): Owning profile id
        params (dict): Single-op params holding a `file_id` and an optional
            `ConvertVideoRequest`-shaped `opts`
        processor (Processor): The conversion orchestrator

    Returns:
        The new MP4 file's id and media URL
    """
    async with UnitOfWork() as uow:
        source = await uow.files.get(uuid.UUID(params["file_id"]))
    src = media.BASE_PATH / source.path
    opts = ConvertVideoRequest.model_validate(params.get("opts") or {})
    out_loc = _converted_out_path(profile_id, source.name)
    rel_out = media.get_relative_path(out_loc)
    await processor.convert_to_mp4(
        src,
        out_loc,
        to_mp4_kwargs=opts.model_dump(exclude_none=True),
    )
    return await _persist_converted(profile_id, rel_out, source=source)


async def _fix_srt(
    profile_id: str,
    params: dict[str, Any],
    processor: Processor,
) -> SrtResult:
    """
    Refines one profile SRT file with an LLM and stores the cleaned result

    Args:
        profile_id (str): Owning profile id
        params (dict): Single-op params holding a `file_id`, a `model`
            selector, and an optional `sys_msg`
        processor (Processor): Unused (the LLM layer is provider-agnostic)

    Returns:
        The new SRT file's id, media URL, and content
    """
    async with UnitOfWork() as uow:
        source = await uow.files.get(uuid.UUID(params["file_id"]))
    src = media.BASE_PATH / source.path
    raw = await asyncio.to_thread(_read_text_best_effort, src)
    client, model = llm.client_for_model(params["model"])
    system = params.get("sys_msg") or get_settings().srt_sys_msg
    fixed = await asyncio.to_thread(
        client.complete,
        system=system,
        prompt=raw,
        model=model,
    )
    fixed = sanitize_srt(fixed)
    return await _persist_srt(profile_id, fixed, source=source, origin="fixed")


# --- Single-Op Handlers ---


async def generate_srt_handler(
    job: JobDTO,
    processor: Processor,
) -> SrtResult:
    """
    Generates raw SRT from a profile video/audio file and stores it

    info: `job`
        Expects a `file_id` and an optional `GenerateSrtRequest`-shaped `opts`
        in the job's `params`

    Args:
        job (JobDTO): The single-op job to run
        processor (Processor): The transcription orchestrator

    Returns:
        The new SRT file's id, media URL, and content
    """
    return await _generate_srt(job.profile_id, job.params, processor)


async def transcribe_handler(
    job: JobDTO,
    processor: Processor,
) -> TranscribeResult:
    """
    Transcribes a profile audio file to joined text and stores a transcript

    info: `job`
        Expects a `file_id` and an optional `TranscribeAudioRequest`-shaped
        `opts` in the job's `params`

    Args:
        job (JobDTO): The single-op job to run
        processor (Processor): The transcription orchestrator

    Returns:
        The new transcript's id and text
    """
    return await _transcribe(job.profile_id, job.params, processor)


async def convert_handler(
    job: JobDTO,
    processor: Processor,
) -> ConvertResult:
    """
    Converts a profile video file to MP4 and stores the result

    info: `job`
        Expects a `file_id` and an optional `ConvertVideoRequest`-shaped `opts`
        in the job's `params`

    Args:
        job (JobDTO): The single-op job to run
        processor (Processor): The conversion orchestrator

    Returns:
        The new MP4 file's id and media URL
    """
    return await _convert(job.profile_id, job.params, processor)


async def fix_srt_handler(
    job: JobDTO,
    processor: Processor,
) -> SrtResult:
    """
    Refines a profile SRT file with an LLM and stores the cleaned result

    info: `job`
        Expects a `file_id`, a `model` selector, and an optional `sys_msg` in
        the job's `params`

    Args:
        job (JobDTO): The single-op job to run
        processor (Processor): Unused (the LLM layer is provider-agnostic)

    Returns:
        The new SRT file's id, media URL, and content
    """
    return await _fix_srt(job.profile_id, job.params, processor)


# --- Batch Bookkeeping ---


async def _load_children(parent_id: uuid.UUID) -> list[JobDTO]:
    """
    Loads a batch parent's child jobs in submit order

    Args:
        parent_id (uuid.UUID): The parent job id

    Returns:
        The child jobs, oldest first
    """
    async with UnitOfWork() as uow:
        return await uow.jobs.list_children(parent_id)


async def _safe_update(job_id: uuid.UUID, **fields: Any) -> None:
    """
    Applies a partial job update, tolerating a row deleted while a job runs

    A batch's parent or child row can be deleted mid-flight (the user deleted
    the job, or a file it relied on cascaded), so a missing row is treated as
    the job being gone rather than an error that would crash the worker and
    log a noisy rollback

    Args:
        job_id (uuid.UUID): The job id to update
        **fields (Any): Fields forwarded to `JobRepository.update`
    """
    async with UnitOfWork() as uow:
        try:
            await uow.jobs.update(job_id, **fields)
        except RecordNotFoundError:
            return
        await uow.commit()


async def _start_child(child_id: uuid.UUID) -> None:
    """
    Marks a child job `running`

    Args:
        child_id (uuid.UUID): The child job id
    """
    await _safe_update(child_id, status="running")


async def _succeed_child(child_id: uuid.UUID, result: JobResult) -> None:
    """
    Marks a child job `succeeded` and records its result

    Args:
        child_id (uuid.UUID): The child job id
        result (JobResult): The child's typed result
    """
    await _safe_update(
        child_id,
        status="succeeded",
        progress=1.0,
        completed=1,
        result=result.model_dump(),
    )


async def _fail_child(
    child_id: uuid.UUID,
    *,
    error: str,
    error_code: str | None,
    error_details: dict[str, Any] | None = None,
) -> None:
    """
    Marks a child job `failed` and records its error

    Args:
        child_id (uuid.UUID): The child job id
        error (str): The failure message
        error_code (str | None): The stable error code
        error_details (dict | None): Structured error context
    """
    await _safe_update(
        child_id,
        status="failed",
        error=error,
        error_code=error_code,
        error_details=error_details,
    )


async def _cancel_child(child_id: uuid.UUID) -> None:
    """
    Marks a child job `cancelled`

    Args:
        child_id (uuid.UUID): The child job id
    """
    await _safe_update(child_id, status="cancelled")


async def _bump_parent(
    parent_id: uuid.UUID,
    *,
    completed: int,
    total: int,
) -> None:
    """
    Advances a batch parent's `completed` count and `progress` fraction

    Args:
        parent_id (uuid.UUID): The parent job id
        completed (int): Number of files finished so far
        total (int): Number of files in the batch
    """
    progress = completed / total if total else 1.0
    await _safe_update(parent_id, completed=completed, progress=progress)


async def _job_cancelled(job_id: uuid.UUID) -> bool:
    """
    Reports whether a job should stop (it was cancelled or deleted)

    Used by batch runners to stop launching more work once the parent is
    cancelled. A deleted job is reported the same way, so the runner also stops
    when the job is removed mid-flight

    Args:
        job_id (uuid.UUID): The job id to check

    Returns:
        `True` if the job's status is `cancelled`, or the job no longer exists
    """
    async with UnitOfWork() as uow:
        try:
            job = await uow.jobs.get(job_id)
        except RecordNotFoundError:
            return True
    return job.status == "cancelled"


async def _fail_orphaned_children(parent_id: uuid.UUID) -> None:
    """
    Fails any of a parent's children left unfinished by a batch-level failure

    info: Batch Failures
        - A batch can fail at the orchestration level
          (e.g. the Modal app or volume fails), which leaves children
          mid-flight while the parent is already marked failed

        - This fails those `queued` / `running` children so none are left
          hanging

        - A single job has no children, so this is a no-op for it

    Args:
        parent_id (uuid.UUID): The failed parent job id
    """
    async with UnitOfWork() as uow:
        children = await uow.jobs.list_children(parent_id)
        for child in children:
            if child.status in ("queued", "running"):
                try:
                    await uow.jobs.update(
                        child.id,
                        status="failed",
                        error="The Batch Failed Before This File Finished",
                        error_code="ServerError",
                    )
                except RecordNotFoundError:
                    continue
        await uow.commit()


class _BatchTally:
    """
    Accumulates a batch's per-file outcomes and keeps the parent in step

    Each recorded outcome advances the parent's `completed` count and
    `progress`, so a polling client watches the batch move file by file. The
    lock serialises those updates when a runner finishes several files
    concurrently

    Attributes:
        parent_id (uuid.UUID): The batch parent job id
        total (int): Number of files in the batch
        succeeded (int): Files finished successfully so far
        failed (int): Files failed so far
        cancelled (int): Files skipped by a cancellation so far
    """

    def __init__(self, parent_id: uuid.UUID, total: int) -> None:
        self.parent_id = parent_id
        self.total = total
        self.succeeded = 0
        self.failed = 0
        self.cancelled = 0
        self._lock = asyncio.Lock()

    @property
    def done(self) -> int:
        """
        The number of files that have reached a terminal state
        """
        return self.succeeded + self.failed + self.cancelled

    async def record(
        self,
        outcome: Literal["succeeded", "failed", "cancelled"],
    ) -> None:
        """
        Records one file's outcome and advances the parent's progress

        Args:
            outcome (Literal): The file's terminal state
        """
        async with self._lock:
            if outcome == "succeeded":
                self.succeeded += 1
            elif outcome == "failed":
                self.failed += 1
            else:
                self.cancelled += 1
            await _bump_parent(
                self.parent_id,
                completed=self.done,
                total=self.total,
            )

    def result(self, children: list[uuid.UUID]) -> BatchResult:
        """
        Builds the parent's aggregate result

        Args:
            children (list[uuid.UUID]): The child job ids, in submit order

        Returns:
            The batch outcome counts and child ids
        """
        return BatchResult(
            total=self.total,
            succeeded=self.succeeded,
            failed=self.failed,
            cancelled=self.cancelled,
            children=[str(child_id) for child_id in children],
        )


# --- Batch Runners ---


async def _run_bounded_batch(
    job: JobDTO,
    children: list[JobDTO],
    processor: Processor,
    core: _PerFileCore,
    concurrency: int,
) -> BatchResult:
    """
    Runs a batch locally by calling a per-file core under a concurrency cap

    info: Concurrency
        - Transcription and conversion pass `concurrency=1`, since the local
          box has a single GPU/CPU, so files run one at a time and reuse the
          cached model / one ffmpeg

        - LLM SRT-fixing passes a higher cap, since the work is I/O-bound
          provider calls

    info: Cancellation
        The parent's status is rechecked before each file starts and again
        before its result is recorded, so a cancel (or a deletion, which reads
        the same way) stops the batch and never resurrects a cancelled child as
        succeeded

    info: Per-File Isolation
        A file's failure is recorded on its own child row and never
        fails the entire batch

    Args:
        job (JobDTO): The batch parent job
        children (list[JobDTO]): The parent's child jobs
        processor (Processor): The orchestrator passed through to the core
        core (_PerFileCore): The single-op core run once per child
        concurrency (int): Maximum files in flight at once

    Returns:
        The batch outcome counts and child ids
    """
    tally = _BatchTally(job.id, len(children))
    sem = asyncio.Semaphore(concurrency)

    async def run_one(child: JobDTO) -> None:
        async with sem:
            if await _job_cancelled(job.id):
                await _cancel_child(child.id)
                await tally.record("cancelled")
                return
            await _start_child(child.id)
            try:
                result = await core(job.profile_id, child.params, processor)
            except MirumojiServerError as exc:
                await _fail_child(
                    child.id,
                    error=str(exc),
                    error_code=exc.code,
                    error_details=exc.details,
                )
                await tally.record("failed")
                return
            except Exception:
                LOGGER.exception(f"Batch Child '{child.id}' Failed")
                await _fail_child(
                    child.id,
                    error="An Unexpected Error Occurred",
                    error_code="ServerError",
                )
                await tally.record("failed")
                return
            if await _job_cancelled(job.id):
                await _cancel_child(child.id)
                await tally.record("cancelled")
                return
            await _succeed_child(child.id, result)
            await tally.record("succeeded")

    await asyncio.gather(*(run_one(child) for child in children))
    return tally.result([child.id for child in children])


async def _store_modal_srt(
    job: JobDTO,
    child: JobDTO,
    outcome: str | MirumojiServerError,
    tally: _BatchTally,
) -> None:
    """
    Stores one fanned-out SRT result onto its child row, honoring cancellation

    Args:
        job (JobDTO): The batch parent job
        child (JobDTO): The child job this result belongs to
        outcome (str | MirumojiServerError): The raw SRT, or the file's failure
        tally (_BatchTally): The batch progress tally
    """
    if await _job_cancelled(job.id):
        await _cancel_child(child.id)
        await tally.record("cancelled")
        return
    if isinstance(outcome, MirumojiServerError):
        await _fail_child(
            child.id,
            error=str(outcome),
            error_code=outcome.code,
            error_details=outcome.details,
        )
        await tally.record("failed")
        return
    try:
        async with UnitOfWork() as uow:
            source = await uow.files.get(uuid.UUID(child.params["file_id"]))
        result = await _persist_srt(
            job.profile_id, outcome, source=source, origin="generated"
        )
    except Exception:
        LOGGER.exception(f"Batch Child '{child.id}' Persist Failed")
        await _fail_child(
            child.id,
            error="An Unexpected Error Occurred",
            error_code="ServerError",
        )
        await tally.record("failed")
        return
    await _succeed_child(child.id, result)
    await tally.record("succeeded")


async def _store_modal_transcript(
    job: JobDTO,
    child: JobDTO,
    file_id: uuid.UUID,
    outcome: str | MirumojiServerError,
    tally: _BatchTally,
) -> None:
    """
    Stores one fanned-out transcript onto its child row, honoring cancellation

    Args:
        job (JobDTO): The batch parent job
        child (JobDTO): The child job this result belongs to
        file_id (uuid.UUID): The transcript's source file id
        outcome (str | MirumojiServerError): The joined text, or the file's
            failure
        tally (_BatchTally): The batch progress tally
    """
    if await _job_cancelled(job.id):
        await _cancel_child(child.id)
        await tally.record("cancelled")
        return
    if isinstance(outcome, MirumojiServerError):
        await _fail_child(
            child.id,
            error=str(outcome),
            error_code=outcome.code,
            error_details=outcome.details,
        )
        await tally.record("failed")
        return
    try:
        result = await _persist_transcript(job.profile_id, file_id, outcome)
    except Exception:
        LOGGER.exception(f"Batch Child '{child.id}' Persist Failed")
        await _fail_child(
            child.id,
            error="An Unexpected Error Occurred",
            error_code="ServerError",
        )
        await tally.record("failed")
        return
    await _succeed_child(child.id, result)
    await tally.record("succeeded")


async def _store_modal_convert(
    job: JobDTO,
    child: JobDTO,
    outcome: Path | MirumojiServerError,
    tally: _BatchTally,
) -> None:
    """
    Records one fanned-out MP4 onto its child row, honoring cancellation

    Args:
        job (JobDTO): The batch parent job
        child (JobDTO): The child job this result belongs to
        outcome (Path | MirumojiServerError): The converted MP4's local path,
            or the file's failure
        tally (_BatchTally): The batch progress tally
    """
    if await _job_cancelled(job.id):
        await _cancel_child(child.id)
        await tally.record("cancelled")
        return
    if isinstance(outcome, MirumojiServerError):
        await _fail_child(
            child.id,
            error=str(outcome),
            error_code=outcome.code,
            error_details=outcome.details,
        )
        await tally.record("failed")
        return
    try:
        rel_out = media.get_relative_path(outcome)
        async with UnitOfWork() as uow:
            source = await uow.files.get(uuid.UUID(child.params["file_id"]))
        result = await _persist_converted(
            job.profile_id, rel_out, source=source
        )
    except Exception:
        LOGGER.exception(f"Batch Child '{child.id}' Persist Failed")
        await _fail_child(
            child.id,
            error="An Unexpected Error Occurred",
            error_code="ServerError",
        )
        await tally.record("failed")
        return
    await _succeed_child(child.id, result)
    await tally.record("succeeded")


async def _run_modal_generate_srt_batch(
    job: JobDTO,
    children: list[JobDTO],
    processor: Processor,
) -> BatchResult:
    """
    Runs a `generate_srt` batch on Modal, fanning the files across containers

    Audio is extracted locally per file, the extractions are transcribed in
    parallel on Modal, and each returned SRT is stored as its container
    finishes

    Args:
        job (JobDTO): The batch parent job
        children (list[JobDTO]): The parent's child jobs
        processor (Processor): The transcription orchestrator

    Returns:
        The batch outcome counts and child ids
    """
    tally = _BatchTally(job.id, len(children))
    child_by_id = {child.id: child for child in children}
    opts = GenerateSrtRequest.model_validate(job.params.get("opts") or {})

    sources: dict[uuid.UUID, Path] = {}
    temps: list[Path] = []
    for child in children:
        try:
            src = await _file_path(uuid.UUID(child.params["file_id"]))
            audio_path, tmp = await _extract_audio(src)
        except MirumojiServerError as exc:
            await _fail_child(
                child.id,
                error=str(exc),
                error_code=exc.code,
                error_details=exc.details,
            )
            await tally.record("failed")
            continue
        except Exception:
            LOGGER.exception(f"Batch Child '{child.id}' Prep Failed")
            await _fail_child(
                child.id,
                error="An Unexpected Error Occurred",
                error_code="ServerError",
            )
            await tally.record("failed")
            continue
        temps.append(tmp)
        await _start_child(child.id)
        sources[child.id] = audio_path

    try:
        if sources:
            results = processor.transcribe_batch(
                sources,
                output_format="srt",
                w_transcribe_args=opts.model_dump(exclude_none=True),
            )
            async for child_id, outcome in results:
                await _store_modal_srt(
                    job,
                    child_by_id[child_id],
                    outcome,
                    tally,
                )
    finally:
        for tmp in temps:
            await _clean_temp(tmp)

    return tally.result([child.id for child in children])


async def _run_modal_transcribe_batch(
    job: JobDTO,
    children: list[JobDTO],
    processor: Processor,
) -> BatchResult:
    """
    Runs a `transcribe` batch on Modal, fanning the files across containers

    Audio is prepared locally per file, transcribed in parallel on Modal, and
    each returned transcript is stored as its container finishes

    Args:
        job (JobDTO): The batch parent job
        children (list[JobDTO]): The parent's child jobs
        processor (Processor): The transcription orchestrator

    Returns:
        The batch outcome counts and child ids
    """
    tally = _BatchTally(job.id, len(children))
    child_by_id = {child.id: child for child in children}
    opts = TranscribeAudioRequest.model_validate(job.params.get("opts") or {})
    w_transcribe_args = opts.model_dump(
        exclude_none=True,
        exclude={"clean_audio"},
    )

    sources: dict[uuid.UUID, Path] = {}
    file_ids: dict[uuid.UUID, uuid.UUID] = {}
    temps: list[Path] = []
    for child in children:
        try:
            file_id = uuid.UUID(child.params["file_id"])
            src = await _file_path(file_id)
            source, tmp = await _filter_audio(
                src,
                clean=opts.clean_audio,
            )
        except MirumojiServerError as exc:
            await _fail_child(
                child.id,
                error=str(exc),
                error_code=exc.code,
                error_details=exc.details,
            )
            await tally.record("failed")
            continue
        except Exception:
            LOGGER.exception(f"Batch Child '{child.id}' Prep Failed")
            await _fail_child(
                child.id,
                error="An Unexpected Error Occurred",
                error_code="ServerError",
            )
            await tally.record("failed")
            continue
        if tmp is not None:
            temps.append(tmp)
        await _start_child(child.id)
        sources[child.id] = source
        file_ids[child.id] = file_id

    try:
        if sources:
            results = processor.transcribe_batch(
                sources,
                output_format="joined",
                w_transcribe_args=w_transcribe_args,
            )
            async for child_id, outcome in results:
                await _store_modal_transcript(
                    job,
                    child_by_id[child_id],
                    file_ids[child_id],
                    outcome,
                    tally,
                )
    finally:
        for tmp in temps:
            await _clean_temp(tmp)

    return tally.result([child.id for child in children])


async def _run_modal_convert_batch(
    job: JobDTO,
    children: list[JobDTO],
    processor: Processor,
) -> BatchResult:
    """
    Runs a `convert` batch on Modal, fanning the files across GPU containers

    Each source video is converted in parallel on Modal and streamed back to
    its destination, then recorded as its container finishes

    Args:
        job (JobDTO): The batch parent job
        children (list[JobDTO]): The parent's child jobs
        processor (Processor): The conversion orchestrator

    Returns:
        The batch outcome counts and child ids
    """
    tally = _BatchTally(job.id, len(children))
    child_by_id = {child.id: child for child in children}
    opts = ConvertVideoRequest.model_validate(job.params.get("opts") or {})

    sources: dict[uuid.UUID, Path] = {}
    out_paths: dict[uuid.UUID, Path] = {}
    for child in children:
        try:
            async with UnitOfWork() as uow:
                file_rec = await uow.files.get(
                    uuid.UUID(child.params["file_id"]),
                )
            src = media.BASE_PATH / file_rec.path
            out_loc = _converted_out_path(job.profile_id, file_rec.name)
        except MirumojiServerError as exc:
            await _fail_child(
                child.id,
                error=str(exc),
                error_code=exc.code,
                error_details=exc.details,
            )
            await tally.record("failed")
            continue
        except Exception:
            LOGGER.exception(f"Batch Child '{child.id}' Prep Failed")
            await _fail_child(
                child.id,
                error="An Unexpected Error Occurred",
                error_code="ServerError",
            )
            await tally.record("failed")
            continue
        await _start_child(child.id)
        sources[child.id] = src
        out_paths[child.id] = out_loc

    if sources:
        results = processor.convert_batch(
            sources,
            out_paths,
            to_mp4_kwargs=opts.model_dump(exclude_none=True),
        )
        async for child_id, outcome in results:
            await _store_modal_convert(
                job,
                child_by_id[child_id],
                outcome,
                tally,
            )

    return tally.result([child.id for child in children])


# --- Batch Handlers ---


async def batch_generate_srt_handler(
    job: JobDTO,
    processor: Processor,
) -> BatchResult:
    """
    Runs a batch of `generate_srt` operations, one child job per file

    The execution strategy is backend-specific. Modal fans the files across
    containers, while the local backend runs them one at a time

    Args:
        job (JobDTO): The batch parent job (its children hold the file ids)
        processor (Processor): The transcription orchestrator

    Returns:
        The batch outcome counts and child ids
    """
    children = await _load_children(job.id)
    if processor.backend == "modal":
        return await _run_modal_generate_srt_batch(job, children, processor)
    return await _run_bounded_batch(job, children, processor, _generate_srt, 1)


async def batch_transcribe_handler(
    job: JobDTO,
    processor: Processor,
) -> BatchResult:
    """
    Runs a batch of `transcribe` operations, one child job per file

    The execution strategy is backend-specific. Modal fans the files across
    containers, while the local backend runs them one at a time

    Args:
        job (JobDTO): The batch parent job (its children hold the file ids)
        processor (Processor): The transcription orchestrator

    Returns:
        The batch outcome counts and child ids
    """
    children = await _load_children(job.id)
    if processor.backend == "modal":
        return await _run_modal_transcribe_batch(job, children, processor)
    return await _run_bounded_batch(job, children, processor, _transcribe, 1)


async def batch_convert_handler(
    job: JobDTO,
    processor: Processor,
) -> BatchResult:
    """
    Runs a batch of `convert` operations, one child job per file

    The execution strategy is backend-specific. Modal fans the files across GPU
    containers, while the local backend runs them one at a time

    Args:
        job (JobDTO): The batch parent job (its children hold the file ids)
        processor (Processor): The conversion orchestrator

    Returns:
        The batch outcome counts and child ids
    """
    children = await _load_children(job.id)
    if processor.backend == "modal":
        return await _run_modal_convert_batch(job, children, processor)
    return await _run_bounded_batch(job, children, processor, _convert, 1)


async def batch_fix_srt_handler(
    job: JobDTO,
    processor: Processor,
) -> BatchResult:
    """
    Runs a batch of `fix_srt` operations, one child job per file

    LLM SRT-fixing is provider-agnostic and I/O-bound, so the files run through
    the bounded-concurrency runner on every backend, capped by the configured
    `max_llm_concurrency`

    Args:
        job (JobDTO): The batch parent job (its children hold the file ids)
        processor (Processor): Unused (the LLM layer is provider-agnostic)

    Returns:
        The batch outcome counts and child ids
    """
    children = await _load_children(job.id)
    return await _run_bounded_batch(
        job,
        children,
        processor,
        _fix_srt,
        get_settings().max_llm_concurrency,
    )


HANDLERS: dict[str, _JobHandler] = {
    "generate_srt": generate_srt_handler,
    "transcribe": transcribe_handler,
    "convert": convert_handler,
    "fix_srt": fix_srt_handler,
    "batch_generate_srt": batch_generate_srt_handler,
    "batch_transcribe": batch_transcribe_handler,
    "batch_convert": batch_convert_handler,
    "batch_fix_srt": batch_fix_srt_handler,
}
"""
Dictionary mapping all currently available `JobHandler` functions to the `type`
attribute of the database-persisted `job` that they execute
"""
