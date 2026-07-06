"""
Defines Pydantic response models for the API's endpoints
"""

from typing import Any

from pydantic import BaseModel

# --- Common Responses ---


class MessageResponse(BaseModel):
    """
    Generic success envelope for endpoints that only confirm an action

    Args:
        success (bool): Whether the action succeeded
        message (str): A short human-readable confirmation
    """

    success: bool
    message: str


# --- Profile Responses ---


class LlmTemplateResponse(BaseModel):
    """
    Response representing a profile's LLM template

    Args:
        id (str): Database ID of the template
        sys_msg (str): System message
        prompt (str): Prompt template
        model (str): Model selector in `provider:model` form
        srt_sys_msg (str): Subtitle-fix system message (empty = server default)
        srt_model (str): Subtitle-fix model override (empty = use `model`)
    """

    id: str
    sys_msg: str
    prompt: str
    model: str
    srt_sys_msg: str = ""
    srt_model: str = ""


class SaveClipResponse(BaseModel):
    """
    Response for the clip-save endpoint

    Args:
        clip_id (str): Database ID of the saved clip
        file_id (str): Database ID of the saved clip's file record
        clip_url (str): Media URL serving the stored clip
    """

    clip_id: str
    file_id: str
    clip_url: str


class ClipResponse(BaseModel):
    """
    Response representing a saved clip

    Args:
        id (str): Database ID of the clip
        file_id (str): Database ID of the clip's file record
        clip_url (str): Media URL serving the clip file
        start_time (float): Clip start time in seconds
        end_time (float): Clip end time in seconds
        breakdown (dict): The saved breakdown payload
    """

    id: str
    file_id: str
    clip_url: str
    start_time: float
    end_time: float
    breakdown: dict[str, Any]


class ProfileFileResponse(BaseModel):
    """
    Response representing a profile file

    Args:
        id (str): Database ID of the file
        name (str): Base file name
        url (str): Media URL serving the file
        type (str | None): Optional file-type tag
        folder (str | None): Optional group label for files uploaded together
        created_at (str | None): ISO-8601 creation timestamp
    """

    id: str
    name: str
    url: str
    type: str | None = None
    folder: str | None = None
    created_at: str | None = None


class ProfileTranscriptResponse(BaseModel):
    """
    Response representing a profile transcript

    Args:
        id (str): Database ID of the transcript
        file_id (str): Database ID of the source file
        text (str): Transcript text
        llm_explanation (str | None): Optional saved LLM explanation
        url (str | None): Media URL serving the source audio, when available
        created_at (str | None): ISO-8601 creation timestamp
    """

    id: str
    file_id: str
    text: str
    llm_explanation: str | None = None
    url: str | None = None
    created_at: str | None = None


class AnkiExportResponse(BaseModel):
    """
    Response for the Anki export endpoint

    Args:
        anki_deck_url (str): Media URL serving the exported deck file
    """

    anki_deck_url: str


# --- Job Responses ---


class JobResponse(BaseModel):
    """
    Response representing a processing job

    Args:
        id (str): Database ID of the job
        type (str): Operation type
        status (str): `queued`, `running`, `succeeded`, `failed`, or
            `cancelled`
        progress (float): Progress fraction in `[0, 1]`
        total (int): Number of work items
        completed (int): Number of finished work items
        parent_id (str | None): Parent batch job id, when this is a child
        result (dict[str, Any] | None): Produced references, or `None` until
            finished
        error (str | None): Failure message when `status` is `failed`
        error_code (str | None): Stable error code on failure (the domain
            exception's code, or `ServerError` for an unexpected failure)
        error_details (dict[str, Any] | None): Structured error context
        created_at (str): ISO-8601 creation timestamp
        updated_at (str): ISO-8601 last-update timestamp
    """

    id: str
    type: str
    status: str
    progress: float
    total: int
    completed: int
    parent_id: str | None = None
    result: dict[str, Any] | None = None
    error: str | None = None
    error_code: str | None = None
    error_details: dict[str, Any] | None = None
    created_at: str
    updated_at: str


# --- Job Results ---


class JobResult(BaseModel):
    """
    Base for a job's typed result payload

    info: Job Results
        - Each `Job Handler` function returns one of these on success

        - The worker stores it on the job's `result` column and it is surfaced
          (as a plain object) in `JobResponse.result`

        - The client narrows them by the job's `type`
    """


class SrtResult(JobResult):
    """
    Result of a `generate_srt` or `fix_srt` job

    Args:
        srt_file_id (str): Database ID of the saved SRT file
        srt_url (str): Media URL serving the stored SRT file
        srt_content (str): The SRT content
    """

    srt_file_id: str
    srt_url: str
    srt_content: str


class TranscribeResult(JobResult):
    """
    Result of a `transcribe` job

    Args:
        transcript_id (str): Database ID of the saved transcript
        transcript (str): The transcription text
    """

    transcript_id: str
    transcript: str


class ConvertResult(JobResult):
    """
    Result of a `convert` job

    Args:
        file_id (str): Database ID of the saved MP4 file
        video_url (str): Media URL serving the converted MP4
    """

    file_id: str
    video_url: str


class BatchResult(JobResult):
    """
    Result of a `batch_*` parent job

    info: Per-File Detail
        - The parent aggregates the outcome counts only

        - Each child job carries its own typed result or error and is fetched
          via `GET /jobs/{id}/children`

    Args:
        total (int): Number of files in the batch
        succeeded (int): Number of files that finished successfully
        failed (int): Number of files that failed
        cancelled (int): Number of files skipped by a cancellation
        children (list[str]): Database IDs of the child jobs, in submit order
    """

    total: int
    succeeded: int
    failed: int
    cancelled: int
    children: list[str]


# --- LLM Responses ---


class ProviderStatusResponse(BaseModel):
    """
    Availability of a single LLM provider

    Args:
        provider (str): The provider id (`openai`, `anthropic`, `gemini`,
            `local`)
        available (bool): Whether the provider is usable in this deployment
    """

    provider: str
    available: bool


class ProvidersResponse(BaseModel):
    """
    Availability of every known LLM provider

    Args:
        providers (list[ProviderStatusResponse]): One entry per provider
    """

    providers: list[ProviderStatusResponse]


class ModelsResponse(BaseModel):
    """
    The models offered by a configured LLM provider

    Args:
        models (list[str]): The available model ids
    """

    models: list[str]


# --- Health Responses ---


class HealthStatusResponse(BaseModel):
    """
    Minimal liveness confirmation

    Args:
        status (str): `ok` while the server is running
    """

    status: str


class SystemInfoResponse(BaseModel):
    """
    Basic information about the system running the server

    Args:
        time (str): Server time in ISO-8601, suffixed with `Z`
        hostname (str): The host name
        platform (str): A terse platform description
        python (str): The Python version
        cpu_cores (int | None): Logical CPU count, or `None` when unknown
        gpu_available (bool): Whether a CUDA GPU is available to transcription
        gpu_name (str): The GPU name, or empty when none
    """

    time: str
    hostname: str
    platform: str
    python: str
    cpu_cores: int | None = None
    gpu_available: bool
    gpu_name: str
