"""
Pydantic Model representing the response of `profile/files`
endpoint.
"""
from pydantic import BaseModel
from typing import Optional


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
    file_type: Optional[str] = None
    created_at: Optional[str] = None
