/**
 * @packageDocumentation Dictionary + tokenizer types (kotobase / fugashi),
 * matching the server's serialized shapes.
 */

/**
 * Token bundling granularity, mirroring the server `BundleMode`. `words` merges
 * into whole dictionary words, `grammar` (default) splits into learning blocks,
 * `morphemes` is one word per raw UniDic unit.
 */
export type BundleMode = "words" | "grammar" | "morphemes";

/**
 * A single sense within a JMdict entry. `pos`/`field`/`misc` carry
 * human-readable labels (expanded server-side), never raw JMdict codes.
 */
export interface WordSense {
    glosses: string[];
    pos: string[];
    field: string[];
    misc: string[];
    antonyms: string[];
    xrefs: string[];
}

/** A JMdict entry. */
export interface JMEntry {
    is_common: boolean;
    freq_rank?: number | null;
    kana: string[];
    kanji: string[];
    senses: WordSense[];
}

/** A JMnedict (proper noun) entry. */
export interface JMNEntry {
    kana: string[];
    kanji: string[];
    name_types: string[];
    gloss: string[];
}

/** A kanji profile (KANJIDIC2 + KRADFILE + KanjiVG). */
export interface KanjiInfo {
    literal: string;
    grade?: number | null;
    stroke_count?: number | null;
    freq?: number | null;
    jlpt?: number | null;
    is_joyo: boolean;
    meanings: string[];
    onyomi: string[];
    kunyomi: string[];
    nanori: string[];
    radicals: string[];
    has_stroke_order: boolean;
}

/**
 * One furigana segment (JmdictFurigana). `ruby` is the written run and `rt`
 * the kana annotation above it; kana-only runs carry no `rt` and render as
 * plain text.
 */
export interface FuriganaSegment {
    ruby: string;
    rt?: string | null;
}

/** A Tatoeba example sentence with its English translations. */
export interface Example {
    text: string;
    translations: string[];
}

/** A search radical (RADKFILE). */
export interface RadicalInfo {
    radical: string;
    stroke_count?: number | null;
}

/**
 * Pronunciation clips available for a kanji (Kanji Alive). Each clip id names
 * one recorded example word, playable via the clip endpoint.
 */
export interface KanjiAudio {
    kanji: string;
    clips: string[];
    fmt: string;
    attribution?: string | null;
}

/** Dictionary data for a single query (`/dict/query`). */
export interface KotobaseData {
    query: string;
    jmentries: JMEntry[];
    jmnentries: JMNEntry[];
    kanji: KanjiInfo[];
    furigana: FuriganaSegment[];
    meanings: string[];
    jlpt: string;
    examples: Example[];
}

/**
 * A morphological short-unit token from the server tokenizer (fugashi /
 * UniDic). Keys match the API's serialized aliases (`kana` = katakana reading).
 */
export interface Token {
    surface: string;
    lemma: string;
    kana: string;
    pos1: string;
    pos2: string;
    pos3: string;
    pos4: string;
    cType: string;
    cForm: string;
    lForm: string;
    orth: string;
    pron: string;
    orthBase: string;
    pronBase: string;
    goshu: string;
    iType: string;
    iForm: string;
    fType: string;
    fForm: string;
}

/**
 * A useful word stitched from one or more UniDic short-unit tokens
 * (`GET /dict/tokenize`). `surface`/`reading` are the pieces joined; `lemma` is
 * the dictionary-lookup form; `tokens` keeps the original short units.
 */
export interface JapaneseWord {
    surface: string;
    reading: string;
    lemma: string;
    pos: string;
    tokens: Token[];
}

/**
 * A {@link JapaneseWord} paired with its dictionary data (`GET /dict/analyze`,
 * and the `focus` of a breakdown).
 */
export interface EnrichedJapaneseWord {
    word: JapaneseWord;
    kotobase_data: KotobaseData;
}
