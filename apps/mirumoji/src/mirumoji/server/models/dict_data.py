from typing import Optional

from pydantic import BaseModel


class WordSense(BaseModel):
    """
    Pydantic Model representing a single sense on a JMDictEntry model

    Args:
      order (int): Sense order of precedence
      pos (str): Sense part of speech
      gloss (str): Sense gloss
    """

    order: int
    pos: str
    gloss: str


class JMEntry(BaseModel):
    """
    Pydantic Model representing a single JMDictEntry for
    a queried word.

    Args:
      rank (int): Priority rank for entry
      kana (list[str]): list of kana readings
      kanji (list[str]): list of kanji readings
      senses (list[WordSense]): list of WordSense models
    """

    rank: int
    kana: list[str]
    kanji: list[str]
    senses: list[WordSense]


class JMNEntry(BaseModel):
    """
    Pydantic Model representing a single JMNeDictEntry for
    a queried word.

    Args:
      kana (list[str]): list of kana readings
      kanji (list[str]): list of kanji readings
      translation_type (str): Type of name
      gloss (list[str]): list of translation strings
    """

    kana: list[str]
    kanji: list[str]
    translation_type: str
    gloss: list[str]


class KanjiInfo(BaseModel):
    """
    Pydantic Model representing a single Kanji entry from KANJIDIC2

    Args:
      literal (str): String of Kanji Literal
      grade (int, optional): Optional Integer of Japanese Grade in which Kanji
                             is learned
      stroke_count (int): Integer representing number of strokes in
                          handwriting.
      meanings (list[str]): list of String representing known meanings.
      onyomi (list[str]): list of strings representing on readings.
      kunyomi (list[str]): list of strings representing kun readings.
      jlpt_kanjidic (int, optional): Optional Integer representing JLPT level
                                     in KANJIDIC2
      jlpt_tanos (int, optional): Optional Integer representing JLPT level in
                                  Tanos list.
    """

    literal: str
    grade: Optional[int]
    stroke_count: int
    meanings: list[str]
    onyomi: list[str]
    kunyomi: list[str]
    jlpt_kanjidic: Optional[int]
    jlpt_tanos: Optional[int]


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


class FocusInfo(BaseModel):
    """
    Pydantic Model representing information about the focus
    word of a sentence breakdown request.

    Args:
      word (str): Word to breakdown.
      reading (str): Word Kana.
      meanings (list[str]): list of meanings for the word.
      jlpt (str): JLPT vocabulary level for the word or 'Unkonwn'
      examples (list[str]): list of example sentences.
    """

    word: str
    reading: str
    meanings: list[str]
    jlpt: str
    examples: list[str]


class DictLookup(BaseModel):
    """
    Pydantic Model representing information
    extracted from kotobase for a query word.

    Args:
      word (str): Query word.
      jmentries (list[JMEntry]): list of JMEntry models.
      jmnentries (list[JMNEntry]): list of JMNEntry models.
      kanji (list[KanjiInfo]): list of KanjiInfo models.
      meanings (list[str]): list of gloss strings from the first entry's sense
      jlpt (str): JLPT vocabulary level for the word or 'Unkonwn'
      examples (list[str]): list of example sentences.
    """

    word: str
    jmentries: list[JMEntry]
    jmnentries: list[JMNEntry]
    kanji: list[KanjiInfo]
    meanings: list[str]
    jlpt: str
    examples: list[str]


class DictWildcardLookup(BaseModel):
    """
    Pydantic Model representing information
    extracted from kotobase for a query word.

    Args:
      pattern (str): Query word.
      jmentries (list[JMEntry]): list of JMEntry models.
      jmnentries (list[JMNEntry]): list of JMNEntry models.
      kanji (list[KanjiInfo]): list of KanjiInfo models.
      examples (list[str]): list of example sentences.
    """

    pattern: str
    jmentries: list[JMEntry]
    jmnentries: list[JMNEntry]
    kanji: list[KanjiInfo]
    examples: list[str]
