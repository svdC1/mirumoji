from pydantic import BaseModel


class AnkiExportResponse(BaseModel):
    anki_deck_url: str
