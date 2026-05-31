"""
Defines Pydantic response models for the API's endpoints
"""

from pydantic import BaseModel

from .jpdict import JapaneseWord
from .llm import GptTemplateBase

# --- LLM responses ---


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


# --- Profile Responses (Deferred) ---


class AnkiExportResponse(BaseModel):
    """
    Response for the Anki export endpoint

    Args:
        anki_deck_url (str): Media URL serving the exported deck file
    """

    anki_deck_url: str


class ClipResponse(BaseModel):
    """
    Response representing a saved clip

    Args:
        id (str): Clip's database ID
        get_url (str): Media URL serving the clip file
        breakdown_response (str): JSON string of the saved breakdown
    """

    id: str
    get_url: str
    breakdown_response: str


class GptTemplateResponse(GptTemplateBase):
    """
    Response representing a profile's prompt template

    Args:
        id (str): The database ID of the template
    """

    id: str


class ProfileFileResponse(BaseModel):
    """
    Response representing a profile file

    Args:
        id (str): The database ID of the file
        file_name (str): Base file name
        get_url (str): Media URL serving the file
        file_type (str | None): Optional file-type tag
        created_at (str | None): Optional creation date
    """

    id: str
    file_name: str
    get_url: str
    file_type: str | None = None
    created_at: str | None = None


class ProfileTranscriptResponse(BaseModel):
    """
    Response representing a profile transcript

    Args:
        id (str): The database ID of the transcript
        transcript (str): Transcript text
        original_file_name (str | None): Optional source audio file name
        gpt_explanation (str | None): Optional saved explanation
        get_url (str | None): Optional media URL serving the audio
        created_at (str | None): Optional creation date
    """

    id: str
    transcript: str
    original_file_name: str | None = None
    gpt_explanation: str | None = None
    get_url: str | None = None
    created_at: str | None = None
