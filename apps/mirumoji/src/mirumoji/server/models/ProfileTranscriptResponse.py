"""
Pydantic Model representing the response of `profile/transcripts`
endpoint.
"""
from pydantic import BaseModel
from typing import Optional


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
    original_file_name: Optional[str] = None
    gpt_explanation: Optional[str] = None
    get_url: Optional[str] = None
    created_at: Optional[str] = None
