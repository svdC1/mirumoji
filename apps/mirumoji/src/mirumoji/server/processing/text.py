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
    BundleMode,
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
        for ne_entry in jmne:
            jmnentries.append(
                JMNEntry(
                    kana=ne_entry.kana or [],
                    kanji=ne_entry.kanji or [],
                    translation_type=ne_entry.translation_type or "",
                    gloss=ne_entry.gloss or [],
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


_ADVERBIAL_NOUN = "副詞可能"
"""
`pos3` marking a noun that can also act adverbially
(今日, 毎日, 去年, 全部, ...)

These stand on their own far more often than they head a compound, so they are
kept out of noun bundles to avoid over-merges like 毎日 + 日本語
"""


_POLITE_AUX = {"です", "ます"}
"""
`orth_base` of the politeness auxiliaries

In `grammar` mode these are split off from the word they politen
(読み | ました, 何 | です) rather than glued onto the stem, since that boundary
is an obvious one for a learner
"""


def _attaches_to_predicate(tok: Token, mode: BundleMode) -> bool:
    """
    Whether a token glues onto an open predicate (verb/adjective) bundle

    Never attaches case/topic particles (`格助詞` を/が/で, `係助詞` は), which
    mark how words relate, so keeping them apart keeps the sentence readable

    abstract: words
        Pulls a predicate's whole tail back onto the stem

        - Form-changing endings: auxiliaries (`助動詞`) for tense,
          politeness and negation (`まし` + `た` in `読み + まし + た` ->
          `読みました`), and suffixes (`接尾辞`) like the `さ` in `高さ`

        - Helper verbs (`動詞`/`非自立可能`): `みる`/`いる` that add nuance
          (the `み` in `食べて + み + た` -> `食べてみた`)

        - The connecting `て`/`で` (`助詞`/`接続助詞`) that links them

    abstract: grammar
        Keeps only the form-changing endings (`助動詞`, `接尾辞`), but splits
        off the parts a learner reads on their own: the polite `ます`/`です`,
        the connecting `て`, and the helper verbs (`食べてみた` ->
        `食べ | て | みた`, and `読みました` -> `読み | ました`)

    Args:
        tok (Token): The candidate following token
        mode (BundleMode): The active bundling mode

    Returns:
        `True` if the token should merge into the current predicate
    """
    if tok.pos == "接尾辞":
        return True
    if mode is BundleMode.grammar:
        # Form-changing endings stay on, but the polite stem breaks off alone
        return tok.pos == "助動詞" and tok.orth_base not in _POLITE_AUX
    # words: glue the whole tail (auxiliaries, helper verbs, connecting て)
    if tok.pos == "助動詞":
        return True
    if tok.pos == "動詞" and tok.pos2 == "非自立可能":
        return True
    return tok.pos == "助詞" and tok.pos2 == "接続助詞"


def _attaches_to_noun(tok: Token) -> bool:
    """
    Whether a token extends an open noun compound

    Japanese builds compound nouns by stacking nouns (and noun-like suffixes)
    with no space between them, so this merges those pieces into one word

    abstract: Merges
        - Another noun/pronoun (`名詞`/`代名詞`): `東京` + `大学` -> `東京大学`

        - A noun-like suffix (`接尾辞`/`名詞的`): the `館` in `図書` + `館` ->
          `図書館`

    abstract: Keeps apart
        - Adverbial nouns (`副詞可能`: 今日, 毎日, ...), which stand alone
          far more often than they head a compound, so merging them would
          wrongly fuse `毎日` + `日本語` into one word

    Args:
        tok (Token): The candidate following token

    Returns:
        `True` if the token should merge into the current noun compound
    """
    if tok.pos in _NOUN_POS:
        return tok.pos3 != _ADVERBIAL_NOUN
    return tok.pos == "接尾辞" and tok.pos2 == "名詞的"


def _bundle_kind(tok: Token, mode: BundleMode) -> str:
    """
    Classifies the kind of bundle a token opens (what it can grow into)

    abstract: Kinds
        - `prefix`: A prefix (`接頭辞`) like `お`/`ご`/`不` attaching to the
          *following* word (the `お` in `お` + `名前` -> `お名前`)

        - `predicate`: A verb/adjective head that absorbs an inflectional tail
          (see `_attaches_to_predicate`). In `grammar` mode a politeness stem
          (`ます`/`です`) also opens one, so it carries its own tense
          (`まし` + `た` -> `ました`) apart from the verb

        - `noun`: A noun/pronoun head that absorbs a compound (see
          `_attaches_to_noun`), unless it is an adverbial noun (`副詞可能`),
          which stays on its own

        - `other`: Anything else (particles like は/を, punctuation, adverbs,
          ...) which stays a standalone one-token word

    Args:
        tok (Token): The bundle's head (first) token
        mode (BundleMode): The active bundling mode

    Returns:
        One of the documented bundle types
    """
    if tok.pos == "接頭辞":
        return "prefix"
    if tok.pos in _PREDICATE_POS:
        return "predicate"
    # In grammar mode a politeness stem heads its own block so it carries its
    # own tense tail (`まし` + `た` -> `ました`), apart from the verb
    if (
        mode is BundleMode.grammar
        and tok.pos == "助動詞"
        and tok.orth_base in _POLITE_AUX
    ):
        return "predicate"
    if tok.pos in _NOUN_POS:
        # Adverbial nouns stay standalone instead of opening a compound
        if tok.pos3 == _ADVERBIAL_NOUN:
            return "other"
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


def stitch(
    tokens: list[Token],
    mode: BundleMode = BundleMode.grammar,
) -> list[JapaneseWord]:
    """
    Stitches UniDic short-unit tokens into useful, learner-facing words

    The grouping is controlled by `mode` (see `BundleMode`)

    example: 私は図書館で本を読みました (grammar mode)
        ```txt
        UniDic short units (10):
            私 | は | 図書 | 館 | で | 本 | を | 読み | まし | た

        Stitched words (8):
            私 | は | 図書館 | で | 本 | を | 読み | ました

        図書 + 館 -> 図書館 (library)
        読み stays on its own, the polite まし + た splits off -> 読み | ました
        Particles は/で/を stay on their own
        ```

    warning: Reliability
        - Splitting verbs, auxiliaries and particles follows directly from
          UniDic's grammatical labels, so it is essentially deterministic

        - Noun compounding is a **heuristic**. UniDic returns a run of nouns,
          not whether they form one word or several (that lives in its
          separate "long unit word" layer, which the short-unit output does
          not expose), so consecutive nouns are merged by rule and may over-
          or under-merge

    Args:
        tokens (list[Token]): Short-unit tokens, in order
        mode (BundleMode): How aggressively to group the tokens

    Returns:
        The stitched `JapaneseWord` bundles, in order
    """
    if mode is BundleMode.morphemes:
        # No stitching, so one word per UniDic short unit
        return [
            _bundle_to_word([tok], _bundle_kind(tok, mode)) for tok in tokens
        ]

    bundles: list[list[Token]] = []
    kinds: list[str] = []

    for tok in tokens:
        if bundles:
            kind = kinds[-1]

            if kind == "predicate" and _attaches_to_predicate(tok, mode):
                bundles[-1].append(tok)
                continue

            if kind == "noun" and _attaches_to_noun(tok):
                bundles[-1].append(tok)
                continue

            if kind == "prefix":
                # A prefix glues onto the following content head and takes that
                # head's kind, otherwise it stands on its own
                new_kind = _bundle_kind(tok, mode)
                if new_kind in {"predicate", "noun", "prefix"}:
                    bundles[-1].append(tok)
                    kinds[-1] = new_kind
                    continue
                kinds[-1] = "other"

        bundles.append([tok])
        kinds.append(_bundle_kind(tok, mode))

    return [
        _bundle_to_word(toks, kind)
        for toks, kind in zip(bundles, kinds, strict=True)
    ]


def segment(
    sentence: str,
    mode: BundleMode = BundleMode.grammar,
) -> list[JapaneseWord]:
    """
    Tokenizes and stitches a sentence into useful words (no dictionary lookups)

    tip: Usage
        - This is the fast path used to render clickable text

        - Since it skips the (relatively slow) dictionary lookups, it is
          suited to tokenising whole subtitles/transcripts

        - The dictionary data is fetched later by `enrich` or on a word click

    Args:
        sentence (str): The Japanese sentence to segment
        mode (BundleMode): How aggressively to group the tokens

    Returns:
        The stitched `JapaneseWord` bundles

    Raises:
        FugashiError: If tokenisation fails
    """
    return stitch(tokenize(sentence), mode)


def segment_batch(
    sentences: list[str],
    mode: BundleMode = BundleMode.grammar,
) -> list[list[JapaneseWord]]:
    """
    Segments many sentences in one call (see `segment`)

    Used to tokenize a whole subtitle file up front in a single request, so the
    player never tokenizes per-cue mid-playback

    Args:
        sentences (list[str]): The sentences to segment, in order
        mode (BundleMode): How aggressively to group the tokens

    Returns:
        One stitched-word list per input sentence, in the same order

    Raises:
        FugashiError: If tokenisation fails
    """
    return [segment(sentence, mode) for sentence in sentences]


def enrich(
    sentence: str,
    mode: BundleMode = BundleMode.grammar,
) -> list[EnrichedJapaneseWord]:
    """
    Segments a sentence and enriches each stitched word with dictionary data

    Runs one `kotobase` lookup per stitched word, keyed on the word's `lemma`.
    Stitching first means a compound like 図書館 (library) is looked up as one
    word and gets a real dictionary entry, instead of looking up the fragments
    図書 and 館 separately (which is both slower and less useful)

    Args:
        sentence (str): The Japanese sentence to process
        mode (BundleMode): How aggressively to group the tokens

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
        for word in segment(sentence, mode)
    ]
