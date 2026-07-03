from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

# --- Bundling Mode ---


class BundleMode(str, Enum):
    """
    How aggressively the `stitch` function groups UniDic short-unit tokens into
    words

    The modes trade granularity for a learner's needs, from whole dictionary
    words down to raw morphemes

    abstract: words
        - The coarsest grouping

        - Merges compound nouns and the whole inflected tail of a predicate,
          including the connecting て, bound auxiliary verbs, and politeness,
          into single dictionary words (e.g. `図書館`, `食べてみたかった`)

        - Best for looking words up

    abstract: grammar (default)
        - The `learning` view

        - Keeps compound nouns and a predicate's inflectional auxiliaries
          together, but breaks off the pieces a learner parses separately,
          like the connecting て, bound auxiliary verbs (みる/いる/出す), and
          the politeness stems (ます/です) (e.g. `食べ | て | みたかった`,
          `読み | ました`)

    abstract: morphemes
        - The finest grouping

        - No stitching at all, one word per UniDic short unit
          (e.g. `図書 | 館`, `読み | まし | た`)
    """

    words = "words"
    grammar = "grammar"
    morphemes = "morphemes"


# --- Kotobase Data Models ---
#
# Flat Pydantic models of kotobase's nested DTOs.
# The server flattens the nested lookup result once (see
# `processing.text.query_kotobase`) so that the frontend can render
# these directly without traversing kotobase's DTO hierarchies.
# Tag codes are expanded into human-readable labels server-side


class JMWordSense(BaseModel):
    """
    Represents a single `sense` (distinct meanings, translations, or nuances
    of a Japanese word) for a word within the Japanese-Multilingual Dictionary

    info: Sense Order
        - Senses are returned in their editorial order

        - They progress from primary, literal definitions to secondary,
          figurative, or technical nuances

        - The order is already preserved in the list returned by kotobase,
          so no explicit field carries it

    info: Readable Tags
        `pos`, `field`, and `misc` carry human-readable labels (e.g.
        `Godan verb with 'u' ending` instead of the raw JMDict code `v5u`),
        expanded server-side

    Args:
        glosses (list[str]): English equivalents for this sense
        pos (list[str]): Readable grammatical classifications
        field (list[str]): Readable subject-domain labels (e.g. medicine)
        misc (list[str]): Readable usage labels (e.g. colloquial, archaic)
        antonyms (list[str]): Antonym cross-references
        xrefs (list[str]): Related-entry cross-references
    """

    glosses: list[str] = Field(default_factory=list)
    pos: list[str] = Field(default_factory=list)
    field: list[str] = Field(default_factory=list)
    misc: list[str] = Field(default_factory=list)
    antonyms: list[str] = Field(default_factory=list)
    xrefs: list[str] = Field(default_factory=list)


class JMEntry(BaseModel):
    """
    Represents a single word entry in the `Japanese-Multilingual Dictionary`

    info: `freq_rank`
        - `Kotobase` derives this field from JMDict's `nfxx` priority tags,
          which split the 24000 most common words into 500-word bands

        - `1` is the most common band and `48` the least, `None` means the
          word is outside the ranked corpus

    Args:
        is_common (bool): Whether any form carries a JMDict common-word
            priority tag
        freq_rank (int | None): The 500-word frequency band, when ranked
        kana (list[str]): Kana reading forms
        kanji (list[str]): Kanji written forms
        senses (list[JMWordSense]): The entry's senses, in editorial order
    """

    is_common: bool = Field(default=False)
    freq_rank: int | None = Field(default=None)
    kana: list[str] = Field(default_factory=list)
    kanji: list[str] = Field(default_factory=list)
    senses: list[JMWordSense] = Field(default_factory=list)


class JMNEntry(BaseModel):
    """
    Represents a single `name` entry in the `Japanese Multi-Lingual
    Dictionary`

    Args:
        kana (list[str]): Kana reading forms
        kanji (list[str]): Kanji written forms
        name_types (list[str]): Readable name-type labels (e.g. surname,
            place name)
        gloss (list[str]): Translation strings
    """

    kana: list[str] = Field(default_factory=list)
    kanji: list[str] = Field(default_factory=list)
    name_types: list[str] = Field(default_factory=list)
    gloss: list[str] = Field(default_factory=list)


class KanjiInfo(BaseModel):
    """
    Represents a single Kanji entry aggregated from `KANJIDIC2`, `KRADFILE`,
    and `KanjiVG`

    info: `jlpt`
        - kotobae exposes both the kanji jlpt level from the `Tanos` study
          lists,  and the pre-2010 `KANJIDIC2` level

        - The server exposes only one aggreagated jlpt level which prefers the
          more updataded `Tanos` level, and falls back to the pre-2010 level
          when the former is not available

    Args:
        literal (str): Kanji literal
        grade (int | None): Optional Japanese grade in which Kanji is learned
        stroke_count (int | None): Number of strokes in handwriting
        freq (int | None): Frequency-of-use rank (1 = most common), when
            ranked
        jlpt (int | None): JLPT level (5 easiest to 1 hardest), when listed
        is_joyo (bool): Whether the Kanji is in the Joyo (regular use) set
        meanings (list[str]): List of known meanings
        onyomi (list[str]): List of `on` readings
        kunyomi (list[str]): List of `kun` readings
        nanori (list[str]): Name-only readings
        radicals (list[str]): The Kanji's radical components (`KRADFILE`)
        has_stroke_order (bool): Whether a `KanjiVG` stroke-order SVG exists
            for this Kanji
    """

    literal: str
    grade: int | None = Field(default=None)
    stroke_count: int | None = Field(default=None)
    freq: int | None = Field(default=None)
    jlpt: int | None = Field(default=None)
    is_joyo: bool = Field(default=False)
    meanings: list[str] = Field(default_factory=list)
    onyomi: list[str] = Field(default_factory=list)
    kunyomi: list[str] = Field(default_factory=list)
    nanori: list[str] = Field(default_factory=list)
    radicals: list[str] = Field(default_factory=list)
    has_stroke_order: bool = Field(default=False)


class FuriganaSegment(BaseModel):
    """
    One segment of a word's furigana segmentation (`JmdictFurigana`)

    info: Rendering
        - `ruby` is the text (kanji or kana) and `rt` is the kana reading
          annotation of that text (appears on top of `ruby` in frontend)

        - Kana-only words carry no `rt`, so they render as plain text

    Args:
        ruby (str): The text (kanji or kana)
        rt (str | None): The kana reading annotation, when the text is kanji
    """

    ruby: str
    rt: str | None = Field(default=None)


class Example(BaseModel):
    """
    A single `Tatoeba` example sentence with its translations

    Args:
        text (str): The Japanese sentence
        translations (list[str]): English translations of the sentence
    """

    text: str
    translations: list[str] = Field(default_factory=list)


class RadicalInfo(BaseModel):
    """
    A single search radical (`RADKFILE`)

    Args:
        radical (str): The radical glyph
        stroke_count (int | None): The radical's stroke count
    """

    radical: str
    stroke_count: int | None = Field(default=None)


class KanjiAudio(BaseModel):
    """
    Pronunciation clips available for a single Kanji (`Kanji Alive`)

    info: Clips
        - `Kanji Alive` records example-word pronunciations per Kanji, so
          each clip id names one recorded example word

        - A clip's bytes are streamed by the audio clip endpoint using its id

    Args:
        kanji (str): The Kanji literal the clips belong to
        clips (list[str]): Clip ids, one per recorded example word
        fmt (str): Audio container format of the clips (e.g. `mp3`)
        attribution (str | None): Attribution string required by the source
            license, when provided
    """

    kanji: str
    clips: list[str] = Field(default_factory=list)
    fmt: str = Field(default="mp3")
    attribution: str | None = Field(default=None)


class KotobaseData(BaseModel):
    """
    Represents all information extracted from `kotobase` for a single
    query (either a single Japanese word, or a wildcard pattern matching
    multiple words)

    info: `meanings`
        - Exposes the English equivalents contained in the first
          Japanese-Multilingual Dictionary entry for the query, one string
          per sense

        - If the query has only `JMNEntry` entries, the first entry's `gloss`
          attribute is used

    Args:
        query (str): query literal (either a single Japanese word or a
            wildcard pattern)
        jmentries (list[JMEntry]): All Japanese-Multilingual Dictionary
            entries for the query
        jmnentries (list[JMNEntry]): All `Japanese-Multilingual Dictionary`
            name entries for the query
        kanji (list[KanjiInfo]): Kanji entries for all Kanji present in the
            query
        furigana (list[FuriganaSegment]): Furigana segmentation of the query
            word's primary form, empty for wildcard queries or unknown words
        meanings (list[str]): All English equivalents contained in the first
            `JMEntry`, or `JMNEntry`
        jlpt (str): JLPT vocabulary level for the word extracted from the
            `Tanos` list. Defaults to `Unknown` when it's a wildcard query or
            the word is not in the list
        examples (list[Example]): Example sentences (with translations)
            containing the single word or any words matched by the wildcard
            query
    """

    query: str
    jmentries: list[JMEntry] = Field(default_factory=list)
    jmnentries: list[JMNEntry] = Field(default_factory=list)
    kanji: list[KanjiInfo] = Field(default_factory=list)
    furigana: list[FuriganaSegment] = Field(default_factory=list)
    meanings: list[str] = Field(default_factory=list)
    jlpt: str = Field(default="Unknown")
    examples: list[Example] = Field(default_factory=list)


# --- Fugashi Data Models ---


class Token(BaseModel):
    """
    Represents morphological data extracted for a single Japanese token

    Maps all core token features and deep UniDic morphological data produced
    by Fugashi. Converts internal dictionary symbols (like asterisks) into
    clean pythonic types.

    Attributes:
        surface (str): The raw string exactly as it appears in the text.
        lemma (str): The dictionary base form (語彙素) of the word.
        reading (str): The standard reading of the token in Katakana.
        pos (str): The broad, top-level part of speech (品詞).
        pos2 (str): Sub-category level 2 part of speech.
        pos3 (str): Sub-category level 3 part of speech.
        pos4 (str): Sub-category level 4 part of speech.
        c_type (str): Conjugation type (活用型) if applicable.
        c_form (str): Conjugation form (活用形) if applicable.
        l_form (str): Lemma reading in Katakana.
        orth (str): Orthographic surface representation.
        pron (str): Actual pronunciation including long vowels.
        orth_base (str): Base form using current orthography.
        pron_base (str): Pronunciation of the base form.
        goshu (str): Word origin type (語種) e.g., Native, Sino-Japanese.
        i_type (str): Word-initial transformation type.
        i_form (str): Word-initial transformation form.
        f_type (str): Word-final transformation type.
        f_form (str): Word-final transformation form.
    """

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    # Core Token Properties
    surface: str = Field(default="", alias="surface")
    lemma: str = Field(default="", alias="lemma")
    reading: str = Field(default="", alias="kana")
    pos: str = Field(default="", alias="pos1")

    # Unidic Morphological Features (from tok.feature)
    pos2: str = Field(default="", alias="pos2")
    pos3: str = Field(default="", alias="pos3")
    pos4: str = Field(default="", alias="pos4")
    c_type: str = Field(default="", alias="cType")
    c_form: str = Field(default="", alias="cForm")
    l_form: str = Field(default="", alias="lForm")
    orth: str = Field(default="", alias="orth")
    pron: str = Field(default="", alias="pron")
    orth_base: str = Field(default="", alias="orthBase")
    pron_base: str = Field(default="", alias="pronBase")
    goshu: str = Field(default="", alias="goshu")
    i_type: str = Field(default="", alias="iType")
    i_form: str = Field(default="", alias="iForm")
    f_type: str = Field(default="", alias="fType")
    f_form: str = Field(default="", alias="fForm")

    @model_validator(mode="before")
    @classmethod
    def clear_asterisks(cls, data: dict[str, Any]) -> dict[str, Any]:
        """
        Cleans incoming dictionary fields by converting UniDic's "*" sentinel
        and any missing (`None`) feature to an empty string, since unknown /
        out-of-vocabulary tokens leave some features unset

        Args:
            data (dict): Raw dictionary data containing morphological fields

        Returns:
            dict: The modified dictionary with "*"/`None` values replaced by ""
        """
        if not isinstance(data, dict):
            return data
        return {
            k: ("" if v is None or v == "*" else v) for k, v in data.items()
        }


# --- Aggregation Models ---


class JapaneseWord(BaseModel):
    """
    Represents a single useful word stitched from one or more UniDic short-unit
    tokens

    abstract: Stitching
        - UniDic segments at the short-unit level, which is often too granular
          to be useful (e.g. `図書館` -> `図書` + `館`, or a verb split from
          its auxiliaries)

        - A `JapaneseWord` re-bundles those short units into the
          word a learner actually wants to click

        - The original short-unit `Token` models are kept in `tokens` so no
          morphological detail is lost

    example: the word built from 読み + まし + た
        - surface = "読みました" (the pieces joined as written)
        - reading = "ヨミマシタ" (their katakana readings joined)
        - lemma = "読む" (the dictionary form, for look-ups)
        - pos = "動詞" (verb -- the head piece's part of speech)
        - tokens = [読み, まし, た] (the three original short units)

    Args:
        surface (str): The bundle's combined surface form
        reading (str): The combined katakana reading of the component tokens
        lemma (str): Dictionary-lookup form (the head token's UniDic's
            `orthBase` for inflected words, or the combined surface for noun
            compounds)
        pos (str): The head token's top-level part of speech
        tokens (list[Token]): The component short-unit tokens, in order
    """

    surface: str
    reading: str
    lemma: str
    pos: str
    tokens: list[Token]


class EnrichedJapaneseWord(BaseModel):
    """
    A `JapaneseWord` paired with its dictionary data

    Returned by the enrichment endpoint (one `kotobase` lookup per stitched
    word), as opposed to the fast tokenize endpoint which returns bare
    `JapaneseWord` models

    Args:
        word (JapaneseWord): The stitched word
        kotobase_data (KotobaseData): The dictionary data for the word's lemma
    """

    word: JapaneseWord
    kotobase_data: KotobaseData
