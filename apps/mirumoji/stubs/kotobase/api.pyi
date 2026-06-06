from .core.datatypes import KanjiDTO, LookupResult, SentenceDTO

class Kotobase:
    def lookup(
        self,
        word: str,
        *,
        wildcard: bool = False,
        include_names: bool = False,
        sentence_limit: int = 50,
        entry_limit: int | None = None
        ) -> LookupResult: ...
    @staticmethod
    def db_info() -> dict[str, str]: ...
    @staticmethod
    def kanji(literal: str) -> KanjiDTO | None: ...
    @staticmethod
    def jlpt_level(word: str) -> int | None: ...
    @staticmethod
    def sentences(text: str, *, limit: int = 20) -> list[SentenceDTO]: ...
    def __call__(
        self,
        word: str,
        *,
        wildcard: bool = False,
        include_names: bool = False,
        sentence_limit: int = 50,
        entry_limit: int | None = None
        ) -> LookupResult: ...

__all__ = ['Kotobase']
