from pydantic import BaseModel

from .jpdict import FocusInfo, Token
from .llm import GptTemplateBase


class AnkiExportResponse(BaseModel):
    """
    Pydantic Model for Anki Export Endpoint Response

    Args:
      anki_deck_url (str): The media URL from FastAPI stactic media serving to
                           the deck file.
    """

    anki_deck_url: str


class BreakdownResponse(BaseModel):
    """
    Pydantic Model for the `/gpt/breakdown` response.

    Args:
      sentence (str): The analyzed sentence.
      focus (FocusInfo): The `FocusInfo` model.
      tokens (list[Token]): list of `Token` models.
      gpt_explanation (str): The GPT API call response.
    """

    sentence: str
    focus: FocusInfo
    tokens: list[Token]
    gpt_explanation: str


class ClipResponse(BaseModel):
    """
    Pydantic Model for the `/profile/clips` request.

    Args:
      id (str): Clip's ID in database.
      get_url (str): URL where FastAPI is serving the stactic file.
      breakdown_response (str): JSON string of `BreakdownResponse` model.
    """

    id: str
    get_url: str
    breakdown_response: str


class GptTemplateResponse(GptTemplateBase):
    """
    Pydantic Model representing the response of `profile/gpt_template`
    endpoint.

    Args:
      id (str): The database ID of the template.
    """

    id: str


class ProfileFileResponse(BaseModel):
    """
    Pydantic Model representing the response of `profile/files`
    endpoint.

    Args:
      id (str): The database ID of the file
      file_name (str): Base file name.
      get_url (str): URL where FastAPI is serving the stactic file.
      file_type (str, optional): Optional information about file.
      created_at (str, optional): Optional creation date information.
    """

    id: str
    file_name: str
    get_url: str
    file_type: str | None = None
    created_at: str | None = None


class ProfileTranscriptResponse(BaseModel):
    """
    Pydantic Model representing the response of `profile/transcripts`
    endpoint.

    Args:
      id (str): The database ID of the transcript
      transcript (str): Transcript text.
      original_file_name (str, optional): Optional name of the audio file
                                          transcribed.
      gpt_explanation (str, optional): Optional GPT explanation for the
                                       transcription if it was created.

      get_url (str, optional): Optional URL where FastAPI is serving the
                               transcribed audio file
      created_at (str, optional): Optional information about creation date.
    """

    id: str
    transcript: str
    original_file_name: str | None = None
    gpt_explanation: str | None = None
    get_url: str | None = None
    created_at: str | None = None
