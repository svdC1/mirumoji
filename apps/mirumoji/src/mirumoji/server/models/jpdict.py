from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

# --- Kotobase Data Models ---


class JMWordSense(BaseModel):
    """
    Represents a single `sense` (distinct meanings, translations, or nuances
    of a Japanese word) for a word within the Japanese-Multilingual Dictionary

    info: `order`
        - Represents the sequential arrangement of word meanings based on
          lexicographical hierarchy

        - Senses progress logically from primary, literal definitions
          to secondary, figurative, or technical nuances

        - This order is editorially curated and does not reflect mathematical
          usage frequency

    Args:
        order (int): editorial priority order
        pos (str):  Grammatical classifications like verb (v5u), noun (n), or
            adjective (adj-no) that apply to this specific meaning
        gloss (str): The English equivalent of the word
    """

    order: int
    pos: str
    gloss: str


class JMEntry(BaseModel):
    """
    Represents a single word entry in the `Japanase-Multilingual Dictionary`

    info: `rank`
        `Kotobase` calculates the `rank` attribute based on JMDict's `<pri>`
        tags. The following are the possible values and their meanings

        - `0` &rarr; High-frequency words found across standard textbooks
          (ichi1) and newspapers (news1)

        - `1-48` &rarr; The specific 500-word corpus interval the word belongs
          to (e.g., tier 5 means the word is within the top `2001-2500` most
          common words)

        - `99` &rarr; Low-priority or niche words containing auxiliary tags

    Args:
        rank (int): A categorized numerical value mapping the word's real-world
            popularity
        kana (list[str] | None): List of kana readings
        kanji (list[str] | None): List of kanji readings
        senses (list[WordSense] | None): List of `JMWordSense` models
    """

    rank: int
    kana: list[str] = Field(default_factory=list)
    kanji: list[str] = Field(default_factory=list)
    senses: list[JMWordSense] = Field(default_factory=list)


class JMNEntry(BaseModel):
    """
    Represents a single `name` entry in the `Japanese Multi-Lingual
    Dictionary`

    Args:
        kana (list[str] | None): List of kana readings
        kanji (list[str] | None): List of kanji readings
        translation_type (str | None): Type of name
        gloss (list[str] | None): list of translation strings
    """

    kana: list[str] = Field(default_factory=list)
    kanji: list[str] = Field(default_factory=list)
    translation_type: str = Field(default="")
    gloss: list[str] = Field(default_factory=list)


class KanjiInfo(BaseModel):
    """
    Represents a single Kanji entry in `KANJIDIC2`

    Args:
        literal (str): Kanji literal
        grade (int | None): Optional Japanese grade in which Kanji is learned
        stroke_count (int | None): Number of strokes in handwriting
        meanings (list[str] | None): List of known meanings
        onyomi (list[str] | None): List of `on` readings
        kunyomi (list[str] | None): List of `kun` readings
        jlpt_kanjidic (int | None): Optional JLPT level present in `KANJIDIC2`
        jlpt_tanos (int | None): Optional JLPT level in `Tanos` list
    """

    literal: str
    grade: int | None = Field(default=None)
    stroke_count: int | None = Field(default=None)
    meanings: list[str] = Field(default_factory=list)
    onyomi: list[str] = Field(default_factory=list)
    kunyomi: list[str] = Field(default_factory=list)
    jlpt_kanjidic: int | None = Field(default=None)
    jlpt_tanos: int | None = Field(default=None)


class KotobaseData(BaseModel):
    """
    Represents all information extracted from `kotobase` for a single
    query (either a single Japanese word, or a wildcard pattern matching
    multiple words)

    info: `meanings`
        - Exposes the `gloss` attributes (English equivalent of the word) of
          all `JMWordSense` models contained inside the first
          Japanase-Multilingual Dictionary entry for the query

        - If the query has only `JMNEntry` entries, the first entry's `gloss`
          attribute is used

    Args:
      query (str): query literal (either a single Japanese word or a wildcard
          pattern)
      jmentries (list[JMEntry]): All Japanese-Multilingual Dictionary entries
          for the query
      jmnentries (list[JMNEntry]): All `Japanese-Multilingual Dictionary`
          name entries for the query
      kanji (list[KanjiInfo]): `KANJIDIC2` entries for all Kanji present in
          the query
      meanings (list[str]): All English equivalents contained in the first
          `JMEntry`, or `JMNEntry`
      jlpt (str): JLPT vocabulary level for the word extracted from the `Tanos`
          list. Defaults to `Unknown` when it's a wildcard query or the word
          is not in the list
      examples (list[str]): List of example sentences containing the single
          word or any words matched by the wildcard query
    """

    query: str
    jmentries: list[JMEntry] = Field(default_factory=list)
    jmnentries: list[JMNEntry] = Field(default_factory=list)
    kanji: list[KanjiInfo] = Field(default_factory=list)
    meanings: list[str] = Field(default_factory=list)
    jlpt: str = Field(default="Unknown")
    examples: list[str] = Field(default_factory=list)


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
