"""
Pydantic Model for the `/profile/clips` request.
"""
from pydantic import BaseModel


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
