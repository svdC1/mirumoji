from pydantic import BaseModel
from typing import Optional


class ProfileFileResponse(BaseModel):
    id: str
    file_name: str
    get_url: str
    file_type: Optional[str] = None
    created_at: Optional[str] = None
