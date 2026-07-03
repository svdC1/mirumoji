"""
Defines functions that use `fugashi` and `kotobase` to tokenize Japanese
sentences and build pydantic models containing relevant dictionary data
"""

from functools import lru_cache

import fugashi
from kotobase import (
    JMDictEntryDTO,
    JMNeDictEntryDTO,
    KanaFormDTO,
    KanjiDTO,
    KanjiFormDTO,
    Kotobase,
    LookupResult,
)

from ...exceptions import FugashiError, KotobaseError
from ..models.jpdict import (
    BundleMode,
    EnrichedJapaneseWord,
    Example,
    FuriganaSegment,
    JapaneseWord,
    JMEntry,
    JMNEntry,
    JMWordSense,
    KanjiAudio,
    KanjiInfo,
    KotobaseData,
    RadicalInfo,
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


# --- Kotobase Mapping (Nested DTOs -> Flat Models) ---


def _readable(codes: list[str], labels: dict[str, str]) -> list[str]:
    """
    Expands raw `JMDict` tag codes into their human-readable labels

    Falls back to the raw code for anything missing from the labels map, so
    that the UI never renders an empty tag

    Args:
        codes (list[str]): Raw tag codes (e.g. `v5u`, `n`)
        labels (dict[str, str]): The lookup's code-to-label map

    Returns:
        The readable label for each code, in order
    """
    return [labels.get(code, code) for code in codes]


def _map_jm_entry(entry: JMDictEntryDTO, labels: dict[str, str]) -> JMEntry:
    """
    Flattens a nested `JMDictEntryDTO` into a `JMEntry`

    Args:
        entry (JMDictEntryDTO): The nested dictionary entry
        labels (dict[str, str]): The lookup's code-to-label map

    Returns:
        The flat `JMEntry`
    """
    return JMEntry(
        is_common=entry.is_common,
        freq_rank=entry.freq_rank,
        kana=[form.text for form in entry.kana],
        kanji=[form.text for form in entry.kanji],
        senses=[
            JMWordSense(
                glosses=[gloss.text for gloss in sense.glosses],
                pos=_readable(sense.pos, labels),
                field=_readable(sense.field, labels),
                misc=_readable(sense.misc, labels),
                antonyms=sense.antonym,
                xrefs=sense.xref,
            )
            for sense in entry.senses
        ],
    )


def _map_jmne_entry(
    entry: JMNeDictEntryDTO,
    labels: dict[str, str],
) -> JMNEntry:
    """
    Flattens a nested `JMNeDictEntryDTO` into a `JMNEntry`

    Args:
        entry (JMNeDictEntryDTO): The nested name entry
        labels (dict[str, str]): The lookup's code-to-label map

    Returns:
        The flat `JMNEntry`
    """
    name_types: list[str] = []
    gloss: list[str] = []
    for translation in entry.translations:
        name_types.extend(_readable(translation.name_type, labels))
        gloss.extend(translation.translations)
    return JMNEntry(
        kana=entry.kana,
        kanji=entry.kanji,
        name_types=name_types,
        gloss=gloss,
    )


def _map_kanji(k: KanjiDTO) -> KanjiInfo:
    """
    Flattens a `KanjiDTO` into a `KanjiInfo`

    The single `jlpt` level prefers the `Tanos` list and falls back to the
    (pre-2010) `KANJIDIC2` level

    Args:
        k (KanjiDTO): The nested Kanji profile

    Returns:
        The flat `KanjiInfo`
    """
    return KanjiInfo(
        literal=k.literal,
        grade=k.grade,
        stroke_count=k.stroke_count,
        freq=k.freq,
        jlpt=k.jlpt_tanos or k.jlpt_old,
        is_joyo=k.is_joyo(),
        meanings=k.meanings,
        onyomi=k.onyomi,
        kunyomi=k.kunyomi,
        nanori=k.nanori,
        radicals=k.radicals,
        has_stroke_order=k.has_stroke_order,
    )


def _map_furigana(result: LookupResult) -> list[FuriganaSegment]:
    """
    Extracts the query word's primary furigana segmentation from a lookup

    Uses the first furigana entry (the primary written form). Kana-only texts
    carry no `rt`, so they render as plain text

    Args:
        result (LookupResult): The kotobase lookup result

    Returns:
        The furigana segments, empty when no segmentation is known
    """
    if not result.furigana:
        return []
    return [
        FuriganaSegment(ruby=seg.get("ruby", ""), rt=seg.get("rt"))
        for seg in result.furigana[0].segments
    ]


# --- Entry Re-Ordering By Relevance ---

_KATA_TO_HIRA = {code: code - 0x60 for code in range(ord("ァ"), ord("ヶ") + 1)}
"""
Translation table shifting the katakana block onto hiragana, so that readings
from UniDic (katakana) compare against JMdict kana forms (mostly hiragana)
"""


def _to_hiragana(text: str) -> str:
    """
    Converts katakana characters in a string to hiragana

    Args:
        text (str): The text to convert

    Returns:
        The text with every katakana character replaced by its hiragana
            counterpart
    """
    return text.translate(_KATA_TO_HIRA)


_UNIDIC_POS_FAMILIES: dict[str, tuple[str, ...]] = {
    "動詞": ("v*",),
    "名詞": ("n", "num", "ctr"),
    "代名詞": ("pn",),
    "形容詞": ("adj-i", "adj-ix"),
    "形状詞": ("adj-na", "adj-t", "adj-no", "adj-nari"),
    "副詞": ("adv",),
    "助詞": ("prt",),
    "助動詞": ("aux", "cop"),
    "接続詞": ("conj",),
    "接頭辞": ("pref",),
    "接尾辞": ("suf", "n-suf", "ctr"),
    "連体詞": ("adj-pn",),
    "感動詞": ("int",),
}
"""
Maps a `UniDic` top-level part of speech to the `JMdict` sense-tag families
that it corresponds to

info: Matches
    - A trailing `*` marks a bare prefix match (every `JMdict` verb code starts
      with `v`)

    - Otherwise, a family matches the exact code or a dashed extension of it
      (`adv` matches `adv` and `adv-to`)
"""


def _pos_family_match(codes: list[str], families: tuple[str, ...]) -> bool:
    """
    Whether any raw `JMdict` sense code belongs to any of the given `UniDic`
    part-of-speech families

    Args:
        codes (list[str]): The sense's raw pos codes
        families (tuple[str, ...]): The families from `_UNIDIC_POS_FAMILIES`

    Returns:
        `True` on the first code that matches a family
    """
    for code in codes:
        for family in families:
            if family.endswith("*"):
                if code.startswith(family[:-1]):
                    return True
            elif code == family or code.startswith(f"{family}-"):
                return True
    return False


_DATED_MISC = frozenset({"arch", "obs", "dated"})
"""
JMdict sense-usage codes marking a sense as no longer in current use
(archaism, obsolete term, dated term)
"""


def _is_kana(text: str) -> bool:
    """
    Whether a string is written entirely in kana

    Args:
        text (str): The text to check

    Returns:
        `True` when every character is hiragana, katakana, or the long-vowel
            mark
    """
    return all(
        "ぁ" <= char <= "ゖ" or char == "ー" for char in _to_hiragana(text)
    )


def _rank_entries(
    entries: list[JMDictEntryDTO],
    query: str,
    reading: str | None,
    pos: str | None,
) -> None:
    """
    Sorts `JMDict` entries returned by kotobase according to their relevance
    to the specific usage of the query which generated them within a specific
    Japanese sentence, by matching the morphological data provided by
    `fugashi` for the query's token within the context of that sentence

    Entries are re-ordered in place by passing the custom `rank` key function
    to the list's `.sort` method. Besides fugashi's morphological data, a few
    other heuristics make sure that more relevant entries appear first, such
    as placing entries whose every sense is marked `archaic` or `dated` below
    entries that are still in use. The reading and part of speech only
    participate when the caller knows them, the form-based signals always do

    info: How The Key Becomes An Ordering
        - `.sort(key=rank)` calls `rank` once per entry and sorts the entries
          by comparing the returned tuples, never the entries themselves

        - Tuples compare lexicographically, so the first position decides the
          order, the second only breaks its ties, and so on down the tuple.
          Each bullet below is therefore strictly more important than
          everything after it

        - `.sort` orders ascending, and booleans compare as integers
          (`False` is `0`, `True` is `1`), so every boolean criterion is
          negated so that a hit becomes `False` and is sorted before the
          misses

        - The count criteria are negated numerically (`-len(...)`) instead,
          so that larger counts sort earlier while staying ascending

        - Python's sort is stable, that is, entries whose whole key tuples tie
          keep kotobase's original order

    info: Ranking
        Entries are ordered by, in priority order

        - Whether the entry has a kana form that matches the token's `reading`
          (disambiguates words that share a written form, like `行った` as
          `いった` vs `おこなった`)

        - Whether the entry is still in use (entries whose every sense is
          tagged `archaic`, `obsolete`, or `dated` sink below living words)

        - Whether the `query` is one of the entry's primary forms,
          as in its headword or first reading (makes sure that entries that
          merely list the `query` as a later variant rank below primary
          entries)

        - Whether a sense's part of speech matches the token's UniDic part of
          speech (a clicked verb ranks verb entries first)

        - For `kana` queries, whether the entry is usually written in kana
          alone (a kana `する` denotes `為る`, not its kanji-written
          homophones, which `JMDict` marks with the `uk` sense tag)

        - Whether the specific form matching the `query` carries a `common`
          flag (more precise than the entry-wide flag when entries share
          forms)

        - The entry-wide `common` flag (whether any form carries a `JMDict`
          priority tag)

        - The entry's sense count (the dominant homophone accumulates senses,
          like `成る` over `生る`, and the `nf` frequency bands cannot
          separate them because the most common words often lack one)

        - How many priority lists (`ichi` / `news` / `spec` / `nf`) carry the
          form that matched the query, as a dominance measure among
          homophones

        - The entry's frequency band (`nf` tags, lower is more common, `99`
          when unranked)

    Args:
        entries (list[JMDictEntryDTO]): The entries to sort, modified in place
        query (str): The looked-up written form
        reading (str | None): The token's reading (any kana), when known
        pos (str | None): The token's UniDic top-level part of speech, when
            known
    """
    # Turn fugashi's katakana reading into hiragana to match JMDict readings
    reading_hira = _to_hiragana(reading) if reading else ""

    # Which JMDict pos tags match the in-context pos reported by fugashi
    families = _UNIDIC_POS_FAMILIES.get(pos or "", ())

    # True if the query is written only in katakana / hiragana
    kana_query = _is_kana(query)

    def rank(
        entry: JMDictEntryDTO,
    ) -> tuple[bool, bool, bool, bool, bool, bool, bool, int, int, int]:
        # 1 - A reading is provided and the entry being analysed has a KanaForm
        # which matches that reading
        form_has_reading = bool(reading_hira) and any(
            _to_hiragana(form.text) == reading_hira for form in entry.kana
        )

        # 2 - Entry has senses and all of them carry an archaic / obsolete /
        # dated usage tag
        is_dated = bool(entry.senses) and all(
            any(code in _DATED_MISC for code in sense.misc)
            for sense in entry.senses
        )

        # The primary forms are the entry's headword and first reading
        primary_texts = [form.text for form in entry.kanji[:1]] + [
            form.text for form in entry.kana[:1]
        ]

        # 3 - The query is one one of the entries primary forms
        query_is_primary_form = query in primary_texts

        # 4 - A fugashi in-context pos was provided, it is one of the mapped
        # pos in `_UNIDIC_POS_FAMILIES`, and one of the entry's senses contains
        # the JMdict pos tags associated with that fugashi pos
        sense_pos_matches_fugashi = bool(families) and any(
            _pos_family_match(sense.pos, families) for sense in entry.senses
        )

        # 5- JMdict tags senses usually written using kana alone with the `uk`
        # tag. This means that the `query` has no kanji (kana-only), and the
        # entry being analysed has at least one sense with a `uk` tag
        has_kana_only_tag = kana_query and any(
            "uk" in sense.misc for sense in entry.senses
        )

        forms: list[KanjiFormDTO | KanaFormDTO] = [
            *entry.kanji,
            *entry.kana,
        ]

        # 6 - The `query` matches one of the entry's kanji / kana forms
        # and that matched form is flagged as common by kotobase
        matched_common = any(
            form.text == query and form.is_common for form in forms
        )

        # 7 - kotobase marks this entry as common
        entry_is_common = entry.is_common

        # 8 - How many senses this entry has. The dominant homophone
        # accumulates senses (成る over 生る), a stronger dominance
        # proxy than the nf frequency bands, which ichi-list words often
        # lack entirely
        entry_sense_count = len(entry.senses)

        # 9 - How many priority codes (ichi / news / spec / nf) the form
        # that matched the query has
        matched_priority = max(
            (len(form.priority) for form in forms if form.text == query),
            default=0,
        )

        # 10 - The entry's frequency rank (nfXX band)
        freq = entry.freq_rank if entry.freq_rank is not None else 99

        return (
            not form_has_reading,
            is_dated,
            not query_is_primary_form,
            not sense_pos_matches_fugashi,
            not has_kana_only_tag,
            not matched_common,
            not entry_is_common,
            -entry_sense_count,
            -matched_priority,
            freq,
        )

    entries.sort(key=rank)


@lru_cache(maxsize=1024)
def query_kotobase(
    query: str,
    wildcard: bool = False,
    include_names: bool = True,
    sentence_limit: int = 5,
    entry_limit: int | None = None,
    reading: str | None = None,
    pos: str | None = None,
) -> KotobaseData:
    """
    Wraps `kotobase.Kotobase.lookup` to provide a lru-cache for queries and
    flatten the nested lookup DTOs into the `KotobaseData` model

    info: Readable Tags
        The lookup runs with `with_labels=True` and every tag code (POS,
        field, misc, name type) is expanded into its human-readable label
        here, so the frontend never handles raw codes

    info: Token-Aware Relevance
        - When the caller knows the token's `reading` and `pos` (from
          fugashi), entries are re-ranked so kana-matching and
          part-of-speech-matching entries come first, which also drives the
          `meanings` summary taken from the top entry

        - A lookup that finds nothing retries once with the hiragana reading,
          so tokens whose written form is not a dictionary key still resolve

    Args:
        query (str): word or wildcard pattern to query
        wildcard (bool): When `True`, allows wildcards to be passed to `query`
            in order to match multiple words
        include_names (bool): When `True`, also includes proper-name entries
            from the `JMNe Dictionary`
        sentence_limit (int): Defines how many `Tatoeba` example sentences to
            fetch
        entry_limit (int | None): Defines the maximum number of JMDict entries
            to fetch. Fetches all entries when set to `None`
        reading (str | None): The token's reading (any kana), when known
        pos (str | None): The token's UniDic top-level part of speech, when
            known

    Returns:
        Pydantic model containing all information extracted from `kotobase`
            for the query word

    Raises:
        KotobaseError: If the `kotobase` lookup fails
    """
    try:
        kb = Kotobase()
        result = kb.lookup(
            query,
            wildcard=wildcard,
            include_names=include_names,
            sentence_limit=sentence_limit,
            entry_limit=entry_limit,
            with_labels=True,
        )

        # Names always belong to the original query form, even when the
        # entry lookup below retries with the reading
        names = list(result.names)

        # Fallback Form - An empty lookup retries with the token's reading
        effective_query = query
        if not result.entries and reading:
            fallback = _to_hiragana(reading)
            if fallback and fallback != query:
                retry = kb.lookup(
                    fallback,
                    wildcard=False,
                    include_names=False,
                    sentence_limit=sentence_limit,
                    entry_limit=entry_limit,
                    with_labels=True,
                )
                if retry.entries:
                    result = retry
                    effective_query = fallback

        _rank_entries(result.entries, effective_query, reading, pos)
        labels = dict(result.labels)

        # Make sure name-type codes expand even if the lookup's labels map
        # does not cover them
        name_codes = sorted(
            {
                code
                for entry in names
                for translation in entry.translations
                for code in translation.name_type
                if code not in labels
            },
        )
        if name_codes:
            labels.update(kb.expand_tags(name_codes))
    except Exception as e:
        raise KotobaseError(
            f"Kotobase Lookup Failed For '{query}' : {e}",
        ) from e

    jmentries = [_map_jm_entry(e, labels) for e in result.entries]
    jmnentries = [_map_jmne_entry(e, labels) for e in names]
    kanji = [_map_kanji(k) for k in result.kanji]

    # Build Meanings from the first available entry (one string per sense)
    meanings: list[str] = []
    if jmentries:
        meanings = [", ".join(sense.glosses) for sense in jmentries[0].senses]
    elif jmnentries:
        meanings = jmnentries[0].gloss

    # Extract JLPT (defaults to "Unknown" when the word isn't in the list)
    jlpt = f"N{result.jlpt_vocab.level}" if result.jlpt_vocab else "Unknown"

    return KotobaseData(
        query=query,
        jmentries=jmentries,
        jmnentries=jmnentries,
        kanji=kanji,
        furigana=_map_furigana(result),
        meanings=meanings,
        jlpt=jlpt,
        examples=[
            Example(text=s.text, translations=s.translations)
            for s in result.sentences
        ],
    )


# --- Kanji Study Lookups ---


def get_kanji(literal: str) -> KanjiInfo | None:
    """
    Fetches the full profile of a single Kanji

    Args:
        literal (str): The Kanji literal

    Returns:
        The flat `KanjiInfo`, or `None` when the Kanji is unknown

    Raises:
        KotobaseError: If the lookup fails
    """
    try:
        k = Kotobase().kanji(literal)
    except Exception as e:
        raise KotobaseError(
            f"Kotobase Kanji Lookup Failed For '{literal}' : {e}",
        ) from e
    return _map_kanji(k) if k else None


def get_stroke_svg(literal: str) -> str | None:
    """
    Fetches a Kanji's stroke-order diagram as a self-contained SVG document
    (`KanjiVG`)

    Args:
        literal (str): The Kanji literal

    Returns:
        The SVG document, or `None` when no stroke-order data exists

    Raises:
        KotobaseError: If the lookup fails
    """
    try:
        return Kotobase().stroke_svg(literal)
    except Exception as e:
        raise KotobaseError(
            f"Kotobase Stroke Lookup Failed For '{literal}' : {e}",
        ) from e


def get_kanji_audio(literal: str) -> KanjiAudio:
    """
    Lists the pronunciation clips available for a Kanji (`Kanji Alive`)

    info: Clips
        - `Kanji Alive` records example-word pronunciations per Kanji, so each
          clip id names one recorded example word

        - The clips list is empty when the optional audio pack is not installed
          or the Kanji has no clips

    Args:
        literal (str): The Kanji literal

    Returns:
        The `KanjiAudio` clip listing

    Raises:
        KotobaseError: If the lookup fails
    """
    try:
        entries = Kotobase().audio(literal)
    except Exception as e:
        raise KotobaseError(
            f"Kotobase Audio Lookup Failed For '{literal}' : {e}",
        ) from e
    first = entries[0] if entries else None
    return KanjiAudio(
        kanji=literal,
        clips=[a.reading for a in entries if a.reading],
        fmt=(first.fmt if first else None) or "mp3",
        attribution=first.attribution if first else None,
    )


def get_audio_clip(literal: str, clip: str) -> tuple[str, bytes] | None:
    """
    Fetches the raw bytes of one pronunciation clip

    Args:
        literal (str): The Kanji literal the clip belongs to
        clip (str): The clip id from `get_kanji_audio`

    Returns:
        The clip's file name and raw bytes, or `None` when no clip matches

    Raises:
        KotobaseError: If the lookup fails
    """
    try:
        payloads = Kotobase().audio_bytes(literal, reading=clip)
    except Exception as e:
        raise KotobaseError(
            f"Kotobase Audio Clip Failed For '{literal}' : {e}",
        ) from e
    return payloads[0] if payloads else None


def _entry_labels(
    kb: Kotobase,
    entries: list[JMDictEntryDTO],
) -> dict[str, str]:
    """
    Builds the code-to-label map for a list of entries

    Collects every tag code carried by the entries' senses (via
    `SenseDTO.all_tags`) and expands them through
    `kotobase.Kotobase.expand_tags`, for the lookups that do not return a
    labels map of their own

    Args:
        kb (Kotobase): The kotobase instance to expand with
        entries (list[JMDictEntryDTO]): The entries whose tags to expand

    Returns:
        The code-to-label map for every tag the entries use
    """
    codes = sorted(
        {
            code
            for entry in entries
            for sense in entry.senses
            for code in sense.all_tags()
        },
    )
    return kb.expand_tags(codes) if codes else {}


def search_english(query: str, limit: int = 50) -> list[JMEntry]:
    """
    Searches dictionary entries by English meaning (reverse lookup)

    Args:
        query (str): The English search text
        limit (int): Maximum number of entries to return

    Returns:
        The matching entries as flat `JMEntry` models

    Raises:
        KotobaseError: If the search fails
    """
    try:
        kb = Kotobase()
        entries = kb.search_meaning(query, limit=limit)
        labels = _entry_labels(kb, entries)
    except Exception as e:
        raise KotobaseError(
            f"Kotobase Meaning Search Failed For '{query}' : {e}",
        ) from e
    return [_map_jm_entry(entry, labels) for entry in entries]


def get_words_with_kanji(literal: str, limit: int = 50) -> list[JMEntry]:
    """
    Lists dictionary entries whose written form uses a Kanji

    Backs the Kanji view's `Words With` section

    Args:
        literal (str): The Kanji literal
        limit (int): Maximum number of entries to return

    Returns:
        The matching entries as flat `JMEntry` models

    Raises:
        KotobaseError: If the lookup fails
    """
    try:
        kb = Kotobase()
        entries = kb.words_with_kanji(literal, limit=limit)
        labels = _entry_labels(kb, entries)
    except Exception as e:
        raise KotobaseError(
            f"Kotobase Words-With-Kanji Failed For '{literal}' : {e}",
        ) from e
    return [_map_jm_entry(entry, labels) for entry in entries]


def get_sentences_with_kanji(literal: str, limit: int = 10) -> list[Example]:
    """
    Lists example sentences that contain a Kanji

    Backs the Kanji view's examples section

    Args:
        literal (str): The Kanji literal
        limit (int): Maximum number of sentences to return

    Returns:
        The matching sentences with their translations

    Raises:
        KotobaseError: If the lookup fails
    """
    try:
        sentences = Kotobase().sentences_with_kanji(literal, limit=limit)
    except Exception as e:
        raise KotobaseError(
            f"Kotobase Sentences-With-Kanji Failed For '{literal}' : {e}",
        ) from e
    return [
        Example(text=s.text, translations=s.translations) for s in sentences
    ]


def resolve_reference(ref: str) -> list[JMEntry]:
    """
    Resolves a sense cross-reference or antonym code into its entries

    Lets the UI turn an xref or antonym string (e.g. `見る・1`) into the
    actual referenced dictionary entries on demand, without resolving every
    reference upfront during a lookup

    Args:
        ref (str): The reference code from a sense's `xrefs` or `antonyms`

    Returns:
        The referenced entries as flat `JMEntry` models

    Raises:
        KotobaseError: If the resolution fails
    """
    try:
        kb = Kotobase()
        entries = kb.resolve_references(ref)
        labels = _entry_labels(kb, entries)
    except Exception as e:
        raise KotobaseError(
            f"Kotobase Reference Resolution Failed For '{ref}' : {e}",
        ) from e
    return [_map_jm_entry(entry, labels) for entry in entries]


@lru_cache(maxsize=1)
def list_radicals() -> list[RadicalInfo]:
    """
    Lists every search radical with its stroke count (`RADKFILE`)

    Cached for the process lifetime, since the radical inventory is static

    Returns:
        All search radicals

    Raises:
        KotobaseError: If the lookup fails
    """
    try:
        radicals = Kotobase().radicals()
    except Exception as e:
        raise KotobaseError(f"Kotobase Radical Listing Failed : {e}") from e
    return [
        RadicalInfo(radical=r.radical, stroke_count=r.stroke_count)
        for r in radicals
    ]


def kanji_by_radicals(
    radicals: tuple[str, ...],
    match: str = "all",
) -> list[KanjiInfo]:
    """
    Finds Kanji that contain one, or every one of the given radicals

    Args:
        radicals (tuple[str, ...]): The radical glyphs to require
        match (str): When `all`, every one of `radicals` must be present in the
            kanji. When `any`, kanjis that contain at least one of `radicals`
            are matched

    Returns:
        The matching Kanji as flat `KanjiInfo` models

    Raises:
        KotobaseError: If the search fails
    """
    try:
        matches = Kotobase().by_radicals(list(radicals), match=match)
    except Exception as e:
        raise KotobaseError(
            f"Kotobase Radical Search Failed For {radicals} : {e}",
        ) from e
    return [_map_kanji(k) for k in matches]


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
            kotobase_data=query_kotobase(
                query=word.lemma,
                reading=word.reading,
                pos=word.pos,
            ),
        )
        for word in segment(sentence, mode)
    ]
