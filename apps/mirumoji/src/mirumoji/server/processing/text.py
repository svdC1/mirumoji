"""
Defines functions that use `fugashi` and `kotobase` to tokenize Japanese
sentences and build pydantic models containing relevant dictionary data
"""

from functools import lru_cache

import fugashi
from kotobase import Kotobase
from kotobase.core.datatypes import JMDictEntryDTO, JMNeDictEntryDTO

from ...exceptions import FugashiError, KotobaseError
from ..models.jpdict import (
    JapaneseWord,
    JMEntry,
    JMNEntry,
    JMWordSense,
    KanjiInfo,
    KotobaseData,
    Token,
)


@lru_cache(maxsize=1)
def _get_tagger() -> fugashi.Tagger:
    """
    Builds and caches a single `fugashi.Tagger`

    The tagger loads the UniDic dictionary on construction, which is
    expensive, so it is built once and reused across calls

    Raises:
        FugashiError: If the tagger cannot be initialised
    """
    try:
        return fugashi.Tagger()
    except Exception as e:
        raise FugashiError(
            f"Failed to Initialise Fugashi : {e}",
        ) from e


def ensure_fugashi() -> None:
    """
    Performs a simple tokenisation operation using `fugashi` to ensure that
    it's functional, raising an exception on any failures

    Raises:
        FugashiError: If any error occurs during tokenisation
    """
    try:
        tagger = _get_tagger()
        tagger("試しに")
    except Exception as e:
        # Raise Initialisation Exception From _get_tagger Unchanged
        if isinstance(e, FugashiError):
            raise e

        raise FugashiError(f"Failed to Tokenise With Fugashi : {e}") from e


def ensure_kotobase() -> None:
    """
    Performs a simple lookup operation using `kotobase` to ensure that
    it's functional, raising an exception on any failures

    Raises:
        KotobaseError: If any error occurs during the lookup
    """
    try:
        kb = Kotobase()
        kb.lookup("試し", wildcard=False, sentence_limit=1)
    except Exception as e:
        raise KotobaseError(
            f"Failed to Properly Initialise Kotobase: {e}"
        ) from e


def tokenize(sentence: str) -> list[Token]:
    """
    Tokenizes a Japanese sentence using `fugashi` and extracts
    all token information into a pydantic model

    Args:
      sentence (str): Sentence to tokenize

    Returns:
        list of `Token` models containing extracted token information
    """
    tagger = _get_tagger()
    tokens: list[Token] = []

    try:
        raw_tokens = list(tagger(sentence))
    except Exception as e:
        raise FugashiError(
            f"Failed to Tokenise Sentence : {e}",
        ) from e

    for tok in raw_tokens:
        # Convert the named tuple of features to a flat dictionary
        token_dict = tok.feature._asdict()

        # Inject surface property since it lives outside tok.feature
        token_dict["surface"] = tok.surface

        # Instantiate Model
        token_model = Token.model_validate(token_dict)
        tokens.append(token_model)

    return tokens


@lru_cache(maxsize=1024)
def query_kotobase(
    query: str,
    wildcard: bool = False,
    include_names: bool = True,
    sentence_limit: int = 5,
    entry_limit: int | None = None,
) -> KotobaseData:
    """
    Wraps `kotobase.Kotobase.lookup` to provide a lru-cache for queries and
    build a pydantic model from the results

    Args:
        query (str): word or wildcard pattern to query
        wildcard (bool): When `True`, allows wildcards to be passed to `query`
            in order to match multiple words
        include_names (bool): When `True`, also includes proper-name entries
            from the `JMNe Dictionary`
        sentence_limit (int): Defines how many `Tatoeba` example sentences to
            fetch
        entry_limit (int | None): Defines the maximum number of combined
            entries (JMDict + JMNeDict) to fetch. Fetches all entries when set
            to `None`

    Returns:
        Pydantic model containing all information extracted from `kotobase`
            for the query word
    """
    try:
        result = Kotobase().lookup(
            word=query,
            wildcard=wildcard,
            include_names=include_names,
            sentence_limit=sentence_limit,
            entry_limit=entry_limit,
        )
    except Exception as e:
        raise KotobaseError(
            f"Kotobase Lookup Failed For '{query}' : {e}",
        ) from e

    # Extract JLPT
    jlpt = f"N{result.jlpt_vocab.level}" if result.jlpt_vocab else None

    # Extract Examples
    examples = [i.text for i in result.examples] if result.examples else None

    jmentries = []
    jmnentries = []
    kanji = []
    meanings = None
    jm_senses = None

    if result.entries:
        filtered = result.filter_entries()
        jm: list[JMDictEntryDTO] = filtered["jmdict"]
        jmne: list[JMNeDictEntryDTO] = filtered["jmnedict"]

        # Build Meanings
        if jm:
            glosses: list[str] = [s["gloss"] for s in jm[0].entries]
            meanings = glosses
        elif jmne:
            meanings = jmne[0].gloss

        # Build JM Entries
        for entry in jm:
            # Build Senses
            if entry.senses:
                jm_senses = [
                    JMWordSense(
                        order=sense["order"],
                        pos=sense["pos"],
                        gloss=sense["gloss"],
                    )
                    for sense in entry.senses
                ]

            jmentries.append(
                JMEntry(
                    rank=entry.rank,
                    kana=entry.kana or None,
                    kanji=entry.kanji or None,
                    senses=jm_senses,
                ),
            )

        # Build JMNe Entries
        for entry in jmne:
            jmnentries.append(
                JMNEntry(
                    kana=entry.kana or None,
                    kanji=entry.kanji or None,
                    translation_type=entry.translation_type or None,
                    gloss=entry.gloss or None,
                ),
            )
    # Build KanjiInfo
    if result.kanji:
        for k in result.kanji:
            kanji.append(
                KanjiInfo(
                    literal=k.literal,
                    grade=k.grade,
                    stroke_count=k.stroke_count or None,
                    meanings=k.meanings or None,
                    onyomi=k.onyomi or None,
                    kunyomi=k.kunyomi or None,
                    jlpt_kanjidic=k.jlpt_kanjidic,
                    jlpt_tanos=k.jlpt_tanos,
                ),
            )

    # Build Final Model
    return KotobaseData(
        query=query,
        jmentries=jmentries or None,
        jmnentries=jmnentries or None,
        kanji=kanji or None,
        meanings=meanings,
        jlpt=jlpt,
        examples=examples,
    )


def process_sentence(sentence: str) -> list[JapaneseWord]:
    """
    Tokenizes a Japanese sentence and extracts information
    from `fugashi` and `kotobase` for every word

    Args:
        sentence (str): The Japanese sentence to process

    Returns:
        A list of pydantic model containing token information extracted from
        `fugashi` and `kotobase`
    """
    tokens = tokenize(sentence)
    data_lst = [query_kotobase(query=tok.surface) for tok in tokens]

    return [
        JapaneseWord(token=tok, kotobase_data=data)
        for tok, data in zip(tokens, data_lst, strict=True)
    ]
