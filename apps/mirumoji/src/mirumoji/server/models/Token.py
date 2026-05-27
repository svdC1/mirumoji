"""
Pydantic Model representing a Token from an analyzed Japanese sentence
"""
from pydantic import BaseModel


class Token(BaseModel):
    """
    Pydantic Model representing a Token from an analyzed Japanese sentence

    Args:
      surface (str): The word as it was written
      lemma (str): Dictionary lemma of word.
      reading (str): Word Kana.
      pos (str): Word's part of speech.
    """
    surface: str
    lemma: str
    reading: str
    pos: str
