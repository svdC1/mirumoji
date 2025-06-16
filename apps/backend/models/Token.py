from pydantic import BaseModel


class Token(BaseModel):
    surface: str
    lemma: str
    reading: str
    pos: str
