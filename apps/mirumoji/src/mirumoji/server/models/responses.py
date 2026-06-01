"""
Defines Pydantic response models for the API's endpoints
"""

from pydantic import BaseModel

from .jpdict import JapaneseWord

# --- LLM Responses ---


class BreakdownResponse(BaseModel):
    """
    Response for the `/llm/breakdown` endpoint

    warning: `focus`
        - For all tokens in a sentence use the `/dict/tokenize` endpoint
          instead

        - This only carries the focused word's `Token` + `KotobaseData` models
          and its LLM explanation within the sentence

    Args:
        focus (JapaneseWord | None): The focused word's token + dictionary
            info, or `None` when no focus was provided
        explanation (str): The LLM explanation
    """

    focus: JapaneseWord | None = None
    explanation: str


class ExplanationResponse(BaseModel):
    """
    Response carrying a single LLM explanation

    Args:
        explanation (str): The LLM explanation
    """

    explanation: str


class FixSrtResponse(BaseModel):
    """
    Response for the `/llm/fix_srt` endpoint

    Args:
        srt (str): The cleaned-up SRT content
    """

    srt: str


# --- Media Responses ---


class AudioTranscriptResponse(BaseModel):
    """
    Response for the `/audio/transcribe` endpoint

    Args:
        transcript_id (str): Database ID of the saved transcript
        transcript (str): The transcription text
        original_file_name (str): Original uploaded file name
        audio_url (str): Media URL serving the stored audio
    """

    transcript_id: str
    transcript: str
    original_file_name: str
    audio_url: str


class GenerateSrtResponse(BaseModel):
    """
    Response for the `/video/generate_srt` endpoint

    Args:
        file_id (str): Database ID of the saved SRT file
        srt_content (str): The raw SRT content
        srt_url (str): Media URL serving the stored SRT file
    """

    file_id: str
    srt_content: str
    srt_url: str


class ConvertVideoResponse(BaseModel):
    """
    Response for the `/video/convert_to_mp4` endpoint

    Args:
        converted_video_url (str): Media URL serving the converted MP4
    """

    converted_video_url: str


# --- Profile Responses ---


class LlmTemplateResponse(BaseModel):
    """
    Response representing a profile's LLM template

    Args:
        id (str): Database ID of the template
        sys_msg (str): System message
        prompt (str): Prompt template
        model (str): Model selector in `provider:model` form
    """

    id: str
    sys_msg: str
    prompt: str
    model: str


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
    breakdown: dict


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
