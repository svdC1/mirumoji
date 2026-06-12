/**
 * @packageDocumentation Dictionary + tokenizer types (kotobase / fugashi),
 * matching the server's serialized shapes.
 */

/** A single sense within a JMdict entry. */
export interface WordSense {
    order: number;
    pos: string;
    gloss: string;
}

/** A JMdict entry. */
export interface JMEntry {
    rank: number;
    kana: string[];
    kanji: string[];
    senses: WordSense[];
}

/** A JMnedict (proper noun) entry. */
export interface JMNEntry {
    kana: string[];
    kanji: string[];
    translation_type: string;
    gloss: string[];
}

/** A KANJIDIC2 entry. */
export interface KanjiInfo {
    literal: string;
    grade?: number | null;
    stroke_count?: number | null;
    meanings: string[];
    onyomi: string[];
    kunyomi: string[];
    jlpt_kanjidic?: number | null;
    jlpt_tanos?: number | null;
}

/** Dictionary data for a single query (`/dict/query`). */
export interface KotobaseData {
    query: string;
    jmentries: JMEntry[];
    jmnentries: JMNEntry[];
    kanji: KanjiInfo[];
    meanings: string[];
    jlpt: string;
    examples: string[];
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
