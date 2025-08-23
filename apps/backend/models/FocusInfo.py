"""
Pydantic Model representing information about the focus
word of a sentence breakdown request.
"""
from pydantic import BaseModel
from typing import List


class FocusInfo(BaseModel):
    """
    Pydantic Model representing information about the focus
    word of a sentence breakdown request.

    Args:
      word (str): Word to breakdown.
      reading (str): Word Kana.
      meanings (List[str]): List of meanings for the word.
      jlpt (str): JLPT vocabulary level for the word or 'Unkonwn'
      examples (List[str]): List of example sentences.
    """
    word: str
    reading: str
    meanings: List[str]
    jlpt: str
    examples: List[str]
