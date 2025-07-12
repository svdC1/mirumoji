"""
Pydantic Model representing information about a wilcard
dictionary lookup pattern used by `/dict/wildcard` endpoint.
"""

from pydantic import BaseModel
from typing import List
from models.JMEntry import JMEntry
from models.JMNEntry import JMNEntry
from models.KanjiInfo import KanjiInfo


class DictWildcardLookup(BaseModel):
    """
    Pydantic Model representing information
    extracted from kotobase for a query word.

    Args:
      pattern (str): Query word.
      jmentries (list): List of JMEntry models.
      jmnentries (list): List of JMNEntry models.
      kanji (list): List of KanjiInfo models.
      examples (list): List of example sentences.
    """
    pattern: str
    jmentries: List[JMEntry]
    jmnentries: List[JMNEntry]
    kanji: List[KanjiInfo]
    examples: List[str]
