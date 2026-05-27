"""
Pydantic Model representing a single Kanji entry from KANJIDIC2
"""

from pydantic import BaseModel
from typing import List, Optional


class KanjiInfo(BaseModel):
    """
    Pydantic Model representing a single Kanji entry from KANJIDIC2

    Args:
      literal (str): String of Kanji Literal
      grade (int, optional): Optional Integer of Japanese Grade in which Kanji
                             is learned
      stroke_count (int): Integer representing number of strokes in
                          handwriting.
      meanings (List[str]): List of String representing known meanings.
      onyomi (List[str]): List of strings representing on readings.
      kunyomi (List[str]): List of strings representing kun readings.
      jlpt_kanjidic (int, optional): Optional Integer representing JLPT level
                                     in KANJIDIC2
      jlpt_tanos (int, optional): Optional Integer representing JLPT level in
                                  Tanos list.
    """
    literal: str
    grade: Optional[int]
    stroke_count: int
    meanings: List[str]
    onyomi: List[str]
    kunyomi: List[str]
    jlpt_kanjidic: Optional[int]
    jlpt_tanos: Optional[int]
