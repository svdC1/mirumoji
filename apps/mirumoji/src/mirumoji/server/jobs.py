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
import uuid
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any, TypeAlias

from ..exceptions import MirumojiServerError
from . import media
from .config import get_settings
from .db import UnitOfWork
from .models.requests import (
    ConvertVideoRequest,
    GenerateSrtRequest,
    TranscribeAudioRequest,
)
from .models.responses import (
    ConvertResult,
    JobResult,
    SrtResult,
    TranscribeResult,
)
from .processing import audio, llm
from .processing.subtitles import sanitize_srt

if TYPE_CHECKING:
    from .db.models import JobDTO
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

LOGGER = logging.getLogger("mirumoji")


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
        result: JobResult | None = None,
        error: str | None = None,
        error_code: str | None = None,
        error_details: dict[str, Any] | None = None,
    ) -> None:
        """
        Persists a job's terminal state to the database

        Args:
            job_id (uuid.UUID): The id of the job to terminate
            result (JobResult | None): The job's successful result
            error (str | None): The message returned by the job on failure
            error_code (str | None): The stable error code on failure
            error_details (dict | None): Structured error context on failure
        """
        async with UnitOfWork() as uow:
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
                    completed=1,
                    result=result.model_dump() if result else {},
                )
            await uow.commit()

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
        # Skip A Job Cancelled While Queued, Otherwise Mark It Running
        # `cancel`` endpoint can only mark the job "cancelled" in the DB, but
        # by then the job's id is already sitting in the in-process
        # asyncio.Queue, and you can't pull a specific item back out of a
        # Queue, so skip it here instead to honor the database status
        async with UnitOfWork() as uow:
            job = await uow.jobs.get(job_id)
            if job.status == "cancelled":
                return
            job = await uow.jobs.update(job_id, status="running")
            await uow.commit()

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
            # Domain Failure - > Surface the stable code + user-facing message
            LOGGER.warning(f"Job '{job_id}' ({job.type}) Failed: {exc.code}")
            await self._terminate_job(
                job_id,
                error=str(exc),
                error_code=exc.code,
                error_details=exc.details,
            )
            return
        except Exception:
            # Unexpected Failure ->Log it, but don't leak the raw message
            LOGGER.exception(f"Job '{job_id}' ({job.type}) Failed")
            await self._terminate_job(
                job_id,
                error="An Unexpected Error Occurred",
                error_code="ServerError",
            )
            return
        # Job Succeeded
        await self._terminate_job(job_id, result=result)

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

        Raises:
            RuntimeError: If the instance's queue hasn't been initialised with
                `start` before the call
        """
        self._ensure_queue()
        async with UnitOfWork() as uow:
            unfinished = await uow.jobs.list_unfinished()
            requeue: list[uuid.UUID] = []
            for job in unfinished:
                if job.status == "running":
                    await uow.jobs.update(
                        job.id,
                        status="failed",
                        error="Interrupted By A Server Restart",
                    )
                else:
                    requeue.append(job.id)
            await uow.commit()

            for job_id in requeue:
                await self.submit_job(job_id)

        LOGGER.info(f"Re-Queued {len(requeue)} job(s)")

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
                for job in unfinished:
                    if job.status == "running":
                        await uow.jobs.update(
                            job.id,
                            status="failed",
                            error="Interrupted By A Server Restart",
                        )
                await uow.commit()
            self._worker_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._worker_task
            self._worker_task = None

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


# --- Handlers ---


async def generate_srt_handler(
    job: JobDTO,
    processor: Processor,
) -> SrtResult:
    """
    Generates raw SRT from a profile video/audio file and stores it

    info: `job`
        To use this handler, a job is expected to contain the following

        - A `file_id` in its `params` attribute / column

        - An optional `models.request.GenerateSrtRequest`-shaped `opts`
          atribute

    Args:
        job (JobDTO): A job containing the aforementioned attributes
        processor (Processor): The transcription orchestrator

    Returns:
        The new SRT file's id, media URL, and content
    """
    src = await _file_path(uuid.UUID(job.params["file_id"]))
    opts = GenerateSrtRequest.model_validate(job.params.get("opts") or {})
    op_id = uuid.uuid4().hex
    tmp = media.get_temp_dir(op_id)
    try:
        ffmpeg = audio.get_ffmpeg_path()["ffmpeg"]
        extracted = await asyncio.to_thread(
            audio.extract_audio,
            ffmpeg,
            str(src),
            str(tmp / f"{op_id}.wav"),
        )
        srt_content = await processor.transcribe(
            extracted,
            output_format="srt",
            w_transcribe_args=opts.model_dump(exclude_none=True),
        )
        srt_loc = media.get_profile_dir(job.profile_id, "subtitles") / (
            f"{op_id}.srt"
        )
        rel_srt = media.get_relative_path(srt_loc)
        await media.write_file(rel_srt, srt_content)
        async with UnitOfWork() as uow:
            rec = await uow.files.add(
                profile_id=job.profile_id,
                name=srt_loc.name,
                path=str(rel_srt),
                type="srt",
            )
            await uow.commit()
        return SrtResult(
            srt_file_id=str(rec.id),
            srt_url=f"/media/{rel_srt.as_posix()}",
            srt_content=srt_content,
        )
    finally:
        await _clean_temp(tmp)


async def transcribe_handler(
    job: JobDTO,
    processor: Processor,
) -> TranscribeResult:
    """
    Transcribes a profile audio file to joined text and stores a transcript

    info: `job`
        To use this handler, a job is expected to contain the following

        - A `file_id` in its `params` attribute / column

        - An optional `models.request.TranscribeAudioRequest`-shaped `opts`
          atribute

    Args:
        job (JobDTO): A job containing the aforementioned attributes
        processor (Processor): The transcription orchestrator

    Returns:
        The new transcript's id and text
    """
    file_id = uuid.UUID(job.params["file_id"])
    src = await _file_path(file_id)
    opts = TranscribeAudioRequest.model_validate(job.params.get("opts") or {})
    w_transcribe_args = opts.model_dump(
        exclude_none=True,
        exclude={"clean_audio"},
    )
    op_id = uuid.uuid4().hex
    tmp = media.get_temp_dir(op_id)
    try:
        source = src
        if opts.clean_audio:
            ffmpeg = audio.get_ffmpeg_path()["ffmpeg"]
            cleaned = tmp / f"cleaned_{op_id}.wav"
            await asyncio.to_thread(
                audio.filter_audio,
                ffmpeg,
                str(src),
                str(cleaned),
            )
            source = cleaned
        text = await processor.transcribe(
            source,
            output_format="joined",
            w_transcribe_args=w_transcribe_args,
        )
        async with UnitOfWork() as uow:
            rec = await uow.transcripts.add(
                profile_id=job.profile_id,
                file_id=file_id,
                text=text,
            )
            await uow.commit()
        return TranscribeResult(transcript_id=str(rec.id), transcript=text)
    finally:
        await _clean_temp(tmp)


async def convert_handler(
    job: JobDTO,
    processor: Processor,
) -> ConvertResult:
    """
    Converts a profile video file to MP4 and stores the result

    info: `job`
        To use this handler, a job is expected to contain the following

        - A `file_id` in its `params` attribute / column

        - An optional `models.request.ConvertVideoRequest`-shaped `opts`
          atribute


    Args:
        job (JobDTO): A job containing the aforementioned attributes
        processor (Processor): The conversion orchestrator

    Returns:
        The new MP4 file's id and media URL
    """
    src = await _file_path(uuid.UUID(job.params["file_id"]))
    opts = ConvertVideoRequest.model_validate(job.params.get("opts") or {})
    op_id = uuid.uuid4().hex
    out_loc = media.get_profile_dir(job.profile_id, "converted") / (
        f"{src.stem}_{op_id}_converted.mp4"
    )
    rel_out = media.get_relative_path(out_loc)
    await processor.convert_to_mp4(
        src,
        out_loc,
        to_mp4_kwargs=opts.model_dump(exclude_none=True),
    )
    async with UnitOfWork() as uow:
        rec = await uow.files.add(
            profile_id=job.profile_id,
            name=out_loc.name,
            path=str(rel_out),
            type="mp4",
        )
        await uow.commit()
    return ConvertResult(
        file_id=str(rec.id),
        video_url=f"/media/{rel_out.as_posix()}",
    )


async def fix_srt_handler(
    job: JobDTO,
    processor: Processor,
) -> SrtResult:
    """
    Refines a profile SRT file with an LLM and stores the cleaned result

    info: `job`
        To use this handler, a job is expected to contain the following
        parameters

        - `file_id` (The SRT File's ID)
        - `model` (Which LLM Provider / Model To Use)
        - `sys_msg` (Optional LLM System Message)

    Args:
        job (JobDTO): A job containing the aforementioned attributes
        processor (Processor): Unused (the LLM layer is provider-agnostic)

    Returns:
        The new SRT file's id, media URL, and content
    """
    src = await _file_path(uuid.UUID(job.params["file_id"]))
    raw = await asyncio.to_thread(src.read_text, encoding="utf-8")
    client, model = llm.client_for_model(job.params["model"])
    system = job.params.get("sys_msg") or get_settings().srt_sys_msg
    fixed = await asyncio.to_thread(
        client.complete,
        system=system,
        prompt=raw,
        model=model,
    )
    fixed = sanitize_srt(fixed)
    op_id = uuid.uuid4().hex
    srt_loc = media.get_profile_dir(job.profile_id, "subtitles") / (
        f"{op_id}_fixed.srt"
    )
    rel_srt = media.get_relative_path(srt_loc)
    await media.write_file(rel_srt, fixed)
    async with UnitOfWork() as uow:
        rec = await uow.files.add(
            profile_id=job.profile_id,
            name=srt_loc.name,
            path=str(rel_srt),
            type="srt",
        )
        await uow.commit()
    return SrtResult(
        srt_file_id=str(rec.id),
        srt_url=f"/media/{rel_srt.as_posix()}",
        srt_content=fixed,
    )


HANDLERS: dict[str, _JobHandler] = {
    "generate_srt": generate_srt_handler,
    "transcribe": transcribe_handler,
    "convert": convert_handler,
    "fix_srt": fix_srt_handler,
}
"""
Dictionary mapping all currently available `JobHandler` functions to the `type`
attribute of the database-persisted `job` that they execute
"""
