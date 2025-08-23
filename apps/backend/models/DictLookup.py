"""
Pydantic Model representing information about a dictionary
lookup word used by `/dict/word` endpoint.
"""
from pydantic import BaseModel
from typing import List
from models.JMNEntry import JMNEntry
from models.JMEntry import JMEntry
from models.KanjiInfo import KanjiInfo


class DictLookup(BaseModel):
    """
    Pydantic Model representing information
    extracted from kotobase for a query word.

    Args:
      word (str): Query word.
      jmentries (List[JMEntry]): List of JMEntry models.
      jmnentries (List[JMNEntry]): List of JMNEntry models.
      kanji (List[KanjiInfo]): List of KanjiInfo models.
      meanings (List[str]): List of gloss strings from the first entry's sense
      jlpt (str): JLPT vocabulary level for the word or 'Unkonwn'
      examples (List[str]): List of example sentences.
    """
    word: str
    jmentries: List[JMEntry]
    jmnentries: List[JMNEntry]
    kanji: List[KanjiInfo]
    meanings: List[str]
    jlpt: str
    examples: List[str]
