"""
Pydantic Model representing a single JMDictEntry for a word.
"""
from pydantic import BaseModel
from typing import List
from models.WordSense import WordSense


class JMEntry(BaseModel):
    """
    Pydantic Model representing a single JMDictEntry for
    a queried word.

    Args:
      rank (int): Priority rank for entry
      kana (List[str]): List of kana readings
      kanji (List[str]): List of kanji readings
      senses (List[WordSense]): List of WordSense models
    """
    rank: int
    kana: List[str]
    kanji: List[str]
    senses: List[WordSense]
