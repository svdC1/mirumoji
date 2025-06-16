from pydantic import BaseModel
from typing import Optional


class ProfileTranscriptResponse(BaseModel):
    id: str
    transcript: str
    original_file_name: Optional[str] = None
    gpt_explanation: Optional[str] = None
    get_url: Optional[str] = None
    created_at: Optional[str] = None
