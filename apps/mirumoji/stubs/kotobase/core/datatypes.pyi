"""
Minimal stubs for `kotobase.core.datatypes` (only what the server uses)
"""

from typing import Any

class Serializable:
    def to_dict(self) -> dict[str, Any]: ...
    def to_json(self, **json_kwargs: dict[str, Any]) -> str: ...
    def __iter__(self) -> Any: ...
    ...

class JMDictEntryDTO(Serializable):
    id: int
    rank: int
    kana: list[str] = ...
    kanji: list[str] = ...
    senses: list[dict[str, Any]] = ...
    ...

class JMNeDictEntryDTO(Serializable):
    id: int
    kana: list[str] = ...
    kanji: list[str] = ...
    translation_type: str = ...
    gloss: list[str] = ...
    ...

class JLPTVocabDTO(Serializable):
    id: int
    level: int
    kanji: str
    hiragana: str
    english: str
    ...

class JLPTKanjiDTO(Serializable):
    id: int
    level: int
    kanji: str
    ...

class JLPTGrammarDTO(Serializable):
    id: int
    level: int
    grammar: str
    formation: str
    examples: list[str] = ...
    ...

class KanjiDTO(Serializable):
    literal: str
    grade: int | None
    stroke_count: int
    meanings: list[str]
    onyomi: list[str]
    kunyomi: list[str]
    jlpt_kanjidic: int | None
    jlpt_tanos: int | None
    ...

class SentenceDTO(Serializable):
    id: int
    text: str
    ...

class LookupResult(Serializable):
    word: str
    entries: list[JMDictEntryDTO | JMNeDictEntryDTO]
    kanji: list[KanjiDTO]
    jlpt_vocab: JLPTVocabDTO | None
    jlpt_kanji_levels: dict[str, int]
    jlpt_grammar: list[JLPTGrammarDTO]
    examples: list[SentenceDTO]
    def has_jlpt(self) -> bool: ...
    def filter_entries(self) -> dict[str, list[Any]]: ...
    ...

__all__ = [
    'JLPTGrammarDTO',
    'JLPTKanjiDTO',
    'JLPTVocabDTO',
    'JMDictEntryDTO',
    'JMNeDictEntryDTO',
    'KanjiDTO',
    'LookupResult',
    'SentenceDTO',
    'Serializable',
]
