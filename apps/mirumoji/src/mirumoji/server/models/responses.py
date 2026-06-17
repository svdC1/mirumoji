"""
Defines Pydantic response models for the API's endpoints
"""

from typing import Any

from pydantic import BaseModel

from .jpdict import EnrichedJapaneseWord

# --- LLM Responses ---


class BreakdownResponse(BaseModel):
    """
    Response for the `/llm/breakdown` endpoint

    warning: `focus`
        - To tokenize a whole sentence use the `/dict/tokenize` endpoint
          instead

        - This only carries the focused word (its stitched token + dictionary
          data) and the LLM explanation of its use within the sentence

    Args:
        focus (EnrichedJapaneseWord | None): The focused word + its dictionary
            data, or `None` when no focus was provided
        explanation (str): The LLM explanation
    """

    focus: EnrichedJapaneseWord | None = None
    explanation: str


class ExplanationResponse(BaseModel):
    """
    Response carrying a single LLM explanation

    Args:
        explanation (str): The LLM explanation
    """

    explanation: str


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
        created_at (str | None): ISO-8601 creation timestamp
    """

    id: str
    name: str
    url: str
    type: str | None = None
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
