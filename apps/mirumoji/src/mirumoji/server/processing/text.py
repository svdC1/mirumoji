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
    EnrichedJapaneseWord,
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

    Raises:
        FugashiError: If the tagger can't be initialised or tokenisation fails
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

    Raises:
        KotobaseError: If the `kotobase` lookup fails
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

    # Extract JLPT (defaults to "Unknown" when the word isn't in the list)
    jlpt = f"N{result.jlpt_vocab.level}" if result.jlpt_vocab else "Unknown"

    # Extract Examples
    examples = [i.text for i in result.examples] if result.examples else []

    jmentries: list[JMEntry] = []
    jmnentries: list[JMNEntry] = []
    kanji: list[KanjiInfo] = []
    meanings: list[str] = []

    if result.entries:
        filtered = result.filter_entries()
        jm: list[JMDictEntryDTO] = filtered["jmdict"]
        jmne: list[JMNeDictEntryDTO] = filtered["jmnedict"]

        # Build Meanings from the first available entry
        if jm:
            meanings = [s["gloss"] for s in jm[0].senses]
        elif jmne:
            meanings = jmne[0].gloss

        # Build JM Entries
        for entry in jm:
            jmentries.append(
                JMEntry(
                    rank=entry.rank,
                    kana=entry.kana or [],
                    kanji=entry.kanji or [],
                    senses=[
                        JMWordSense(
                            order=sense["order"],
                            pos=sense["pos"],
                            gloss=sense["gloss"],
                        )
                        for sense in (entry.senses or [])
                    ],
                ),
            )

        # Build JMNe Entries
        for entry in jmne:
            jmnentries.append(
                JMNEntry(
                    kana=entry.kana or [],
                    kanji=entry.kanji or [],
                    translation_type=entry.translation_type or "",
                    gloss=entry.gloss or [],
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
                    meanings=k.meanings or [],
                    onyomi=k.onyomi or [],
                    kunyomi=k.kunyomi or [],
                    jlpt_kanjidic=k.jlpt_kanjidic,
                    jlpt_tanos=k.jlpt_tanos,
                ),
            )

    # Build Final Model (collections are always present, never null)
    return KotobaseData(
        query=query,
        jmentries=jmentries,
        jmnentries=jmnentries,
        kanji=kanji,
        meanings=meanings,
        jlpt=jlpt,
        examples=examples,
    )


# --- Stitching (UniDic Short-Unit -> Useful Word) ---
#
# UniDic segments text into "short unit words" (SUW), the smallest meaningful
# pieces. That is often too granular for a learner, since it splits a single
# dictionary word across several pieces. For example, 読みました (yomimashita,
# the polite past of 読む "to read") comes back as (読み + まし + た), and
# 図書館 (toshokan, "library") comes back as (図書 + 館 ).
# Stitching merges those pieces back into the word a learner actually
# wants to click on, using the grammatical labels UniDic assigns each piece


_PREDICATE_POS = {"動詞", "形容詞", "形状詞"}
"""
Set of parts-of-speech that indicate a predicate (words that change form for
tense, politeness, negation, ...) when present in a token

info : Additional Information
    - A Token's `pos` is its top-level part of speech (品詞)

    - Examples are verbs (動詞), i-adjectives (形容詞), and na-adjectives
      (形状詞)

    - A predicate is what a stitched word grows from when gluing on its
      inflectional tail

"""


_NOUN_POS = {"名詞", "代名詞"}
"""
Parts of speech that head common/proper nouns (名詞), and pronouns (代名詞)

These open a (possibly compound) noun bundle
"""


def _attaches_to_predicate(tok: Token) -> bool:
    """
    Whether a token glues onto an open predicate (verb/adjective) bundle

    Deliberately does NOT attach case/topic particles (`格助詞` を/が/で,
    `係助詞` は), since those mark how words relate and should stay separate so
    that the sentence structure stays visible


    abstract: Open Predicates
        A predicate's meaning is spread across its stem + a tail of
        grammatical pieces. This merges that tail back on by returning `True`
        for the following parts of speech

        - Auxiliaries (`助動詞`) &rarr; carry tense/politeness/negation (e.g.
          the `まし` and `た` in `読み + まし + た` -> `読みました`)

        - Suffixes (`接尾辞`) &rarr; e.g. `さ` turning an adjective into a noun

        - Bound auxiliary verbs (`動詞`/`非自立可能`) &rarr; verbs like `いる`,
          `みる`, `くる` that follow another verb to add aspect/nuance (e.g.
          the `み` from `みる` in `食べて` + `み` + `た` -> `食べてみた`)

        - The connecting particle て/で (`助詞`/`接続助詞`) that links the
          above (e.g. the `て` in `食べ` + `て` + `みた`)

    Args:
        tok (Token): The candidate following token

    Returns:
        `True` if the token should merge into the current predicate
    """
    if tok.pos in {"助動詞", "接尾辞"}:
        return True
    if tok.pos == "動詞" and tok.pos2 == "非自立可能":
        return True
    return tok.pos == "助詞" and tok.pos2 == "接続助詞"


def _attaches_to_noun(tok: Token) -> bool:
    """
    Whether a token extends an open noun compound

    Japanese builds compound nouns by stacking nouns (and noun-like suffixes)
    with no space between them. This merges those pieces into one word

    info: Additional Information
        Returns `True` for the following parts of speech

        - Another noun/pronoun (`名詞`/`代名詞`) &rarr; (e.g. `東京` / Tokyo +
          `大学` / University -> `東京大学` / Tokyo University)

        - A noun-like suffix (`接尾辞`/`名詞的`) &rarr; (e.g. the `館` /
          building in `図書` + `館` -> `図書館` / library)

    Args:
        tok (Token): The candidate following token

    Returns:
        `True` if the token should merge into the current noun compound
    """
    if tok.pos in _NOUN_POS:
        return True
    return tok.pos == "接尾辞" and tok.pos2 == "名詞的"


def _bundle_kind(tok: Token) -> str:
    """
    Classifies the kind of bundle a token opens (what it can grow into)

    abstract: Bundle Types
        - `prefix` &rarr; A prefix (`接頭辞`) like `お`/`ご`/`不` that attaches
          to the *following* word (e.g. the `お` in `お` + `名前` -> `お名前`)

        - `predicate` &rarr; A verb/adjective head that can absorb an
          inflectional tail (see `_attaches_to_predicate`)

        - `noun` &rarr; A noun/pronoun head that can absorb a compound (see
          `_attaches_to_noun`)

        - `other` &rarr; Anything else (particles like は/を, punctuation,
          adverbs, ...) which stays a standalone one-token word

    Args:
        tok (Token): The bundle's head (first) token

    Returns:
        One of the documented bundle types
    """
    if tok.pos == "接頭辞":
        return "prefix"
    if tok.pos in _PREDICATE_POS:
        return "predicate"
    if tok.pos in _NOUN_POS:
        return "noun"
    return "other"


def _bundle_to_word(toks: list[Token], kind: str) -> JapaneseWord:
    """
    Builds a single `JapaneseWord` from a run of stitched short-unit tokens

    info: `surface` + `reading`
       These are simply the pieces concatenated in order

    info: `lemma`
        The form used to look the word up in the dictionary, chosen according
        to the following rules so that inflected and compound words both
        resolve cleanly

        - Inflected predicates and single tokens use the head's written base
          form (`orthBase`), which is the from that the dictionary is keyed on,
          rather the inflected surface. For example,
          `読み` (inflected surface) -> `読む` (orthBase)

        - Multi-token noun compounds use the combined surface, so `図書` + `館`
          is looked up as the whole word `図書館` rather than as `図書` alone

    Args:
        toks (list[Token]): The component tokens, in order
        kind (str): The bundle kind from `_bundle_kind`

    Returns:
        The stitched `JapaneseWord`
    """
    head = toks[0]
    surface = "".join(t.surface for t in toks)
    reading = "".join(t.reading for t in toks)
    if kind == "noun" and len(toks) > 1:
        lemma = surface
    else:
        lemma = head.orth_base or head.surface
    return JapaneseWord(
        surface=surface,
        reading=reading,
        lemma=lemma,
        pos=head.pos,
        tokens=toks,
    )


def stitch(tokens: list[Token]) -> list[JapaneseWord]:
    """
    Stitches UniDic short-unit tokens into useful, learner-facing words

    example: Tokenisation Example
        ```txt
        私は図書館で本を読みました (I read a book at the library)

        UniDic short units (10):
            私 | は | 図書 | 館 | で | 本 | を | 読み | まし | た

        Stitched words (7):
            私 | は | 図書館 | で | 本 | を | 読みました

        Changes:

            図書 + 館 -> 図書館 (Library)
            読み + まし + た -> 読みました (Read - Polite Form)
            Particles は/で/を Stay On Their Own
        ```

    warning: Reliability

        - Predicate gluing (verb/adjective + its auxiliaries, bound verbs,
          and connecting て/で) follows directly from UniDic's grammatical
          labels, so it is essentially deterministic

        - Noun compounding is a **heuristic**. UniDic hands back a run of
          nouns, but does not say whether they form one compound or several
          words (that lives in its separate "long unit word" layer, which the
          short-unit output doesn't expose), so consecutive nouns are merged
          by rule and may occasionally over- or under-merge

    Args:
        tokens (list[Token]): Short-unit tokens, in order

    Returns:
        The stitched `JapaneseWord` bundles, in order
    """
    bundles: list[list[Token]] = []
    kinds: list[str] = []

    for tok in tokens:
        if bundles:
            kind = kinds[-1]

            if kind == "predicate" and _attaches_to_predicate(tok):
                bundles[-1].append(tok)
                continue

            if kind == "noun" and _attaches_to_noun(tok):
                bundles[-1].append(tok)
                continue

            if kind == "prefix":
                # A prefix glues onto the following content head, then takes
                # that head's kind; otherwise it stands on its own
                new_kind = _bundle_kind(tok)
                if new_kind in {"predicate", "noun", "prefix"}:
                    bundles[-1].append(tok)
                    kinds[-1] = new_kind
                    continue
                kinds[-1] = "other"

        bundles.append([tok])
        kinds.append(_bundle_kind(tok))

    return [
        _bundle_to_word(toks, kind)
        for toks, kind in zip(bundles, kinds, strict=True)
    ]


def segment(sentence: str) -> list[JapaneseWord]:
    """
    Tokenizes and stitches a sentence into useful words (no dictionary lookups)

    tip: Usage
        - This is the fast path used to render clickable text

        - Since it skips the (relatively slow) dictionary lookups, it is
          suited to tokenising whole subtitles/transcripts

        - The dictionary data is fetched later by `enrich` or on a word click

    Args:
        sentence (str): The Japanese sentence to segment

    Returns:
        The stitched `JapaneseWord` bundles

    Raises:
        FugashiError: If tokenisation fails
    """
    return stitch(tokenize(sentence))


def segment_batch(sentences: list[str]) -> list[list[JapaneseWord]]:
    """
    Segments many sentences in one call (see `segment`)

    Used to tokenize a whole subtitle file up front in a single request, so the
    player never tokenizes per-cue mid-playback

    Args:
        sentences (list[str]): The sentences to segment, in order

    Returns:
        One stitched-word list per input sentence, in the same order

    Raises:
        FugashiError: If tokenisation fails
    """
    return [segment(sentence) for sentence in sentences]


def enrich(sentence: str) -> list[EnrichedJapaneseWord]:
    """
    Segments a sentence and enriches each stitched word with dictionary data

    Runs one `kotobase` lookup per stitched word, keyed on the word's `lemma`.
    Stitching first means a compound like 図書館 (library) is looked up as one
    word and gets a real dictionary entry, instead of looking up the fragments
    図書 and 館 separately (which is both slower and less useful)

    Args:
        sentence (str): The Japanese sentence to process

    Returns:
        A list of `EnrichedJapaneseWord` (stitched word + dictionary data)

    Raises:
        FugashiError: If tokenisation fails
        KotobaseError: If a dictionary lookup fails
    """
    return [
        EnrichedJapaneseWord(
            word=word,
            kotobase_data=query_kotobase(query=word.lemma),
        )
        for word in segment(sentence)
    ]
