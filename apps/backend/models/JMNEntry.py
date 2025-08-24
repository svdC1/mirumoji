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
      kana (List[str]): List of kana readings
      kanji (List[str]): List of kanji readings
      translation_type (str): Type of name
      gloss (List[str]): List of translation strings
    """
    kana: List[str]
    kanji: List[str]
    translation_type: str
    gloss: List[str]
