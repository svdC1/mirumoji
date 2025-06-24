"""
Pydantic Model for Anki Export Endpoint Response
"""
from pydantic import BaseModel


class AnkiExportResponse(BaseModel):
    """
    Pydantic Model for Anki Export Endpoint Response

    Args:
      anki_deck_url (str): The media URL from FastAPI stactic media serving to
                           the deck file.
    """
    anki_deck_url: str
