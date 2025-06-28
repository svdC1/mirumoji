"""
Pydantic Model representing a single JMNeDictEntry for a word.
"""
from pydantic import BaseModel
from typing import List


class JMNEntry(BaseModel):
    """
    Pydantic Model representing a single JMNeDictEntry for
    a queried word.

    Args:
      kana (list): List of kana readings
      kanji (list): List of kanji readings
      translation_type (str): Type of name
      gloss (list): List of translation strings
    """
    kana: List[str]
    kanji: List[str]
    translation_type: str
    gloss: List[str]
