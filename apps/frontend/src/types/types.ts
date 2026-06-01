/**
 * @packageDocumentation This file contains all the type definitions for the application.
 */

import { Tokenizer, IpadicFeatures } from "kuromoji";

/* UserPage*/

/**
 * The shape of a GPT template.
 */
export interface GptTemplate {
    id: string;
    sysMsg: string;
    prompt: string;
    version: string;
}

/**
 * The shape of a profile file.
 */
export type ProfileFile = {
    id: string;
    file_name: string;
    get_url: string;
    file_type: string;
};

/**
 * The shape of a profile transcript.
 */
export type ProfileTranscript = {
    id: string;
    original_file_name?: string;
    transcript: string;
    gpt_explanation?: string;
    get_url: string;
};

/* SettingsDrawer*/

/**
 * The props for the SettingsDrawer component.
 */
export interface SettingsDrawerProps {
    video: File | null;
    srt: File | null;
    onVideo: (file: File | null) => void;
    onVideoUrl?: (url: string) => void;
    onSrt: (file: File | null) => void;
    onClose: () => void;
    showFurigana: boolean;
    onToggleFurigana: () => void;
}

/**
 * The shape of the response from the generate SRT endpoint.
 */
export interface GenerateSrtResponse {
    srt_content: string;
}

/**
 * The shape of the response from the convert video endpoint.
 */
export interface ConvertVideoResponse {
    converted_video_url: string;
}

/* WordDialog*/

/**
 * The shape of the response from the save clip endpoint.
 */
export interface SaveClipResponse {
    success: boolean;
    message: string;
    clip_id?: string;
}

/* SavedPage*/

/**
 * The shape of a clip.
 */
export type Clip = {
    id: string;
    get_url: string;
    breakdown_response: string;
    sentence_preview?: string;
    gpt_explanation_preview?: string;
};

/**
 * The shape of the focus of a breakdown.
 */
export interface BreakdownFocus {
    word: string;
    reading: string;
    meanings: string[];
    jlpt?: string;
    examples?: any[];
}

/**
 * The shape of a breakdown response from the API
 */
export interface BreakdownData {
    sentence: string;
    focus: BreakdownFocus;
    tokens: any[];
    gpt_explanation: string;
}

/**
 * The shape of the response from the Anki export endpoint.
 */
export interface AnkiExportResponse {
    anki_deck_url: string;
}

/*SubtitlePlayer */

/**
 * The shape of a subtitle cue.
 */
export interface Cue {
    start: number;
    end: number;
    tokens: IpadicFeatures[];
    raw: string;
}

/**
 * The props for the SubtitlePlayer component.
 */
export interface SubtitlePlayerProps {
    video: File;
    videoUrl?: string;
    srt: File | null;
    showFurigana: boolean;
}

/*WordDialog */

/**
 * The props for the WordDialog component.
 */
export interface WordDialogProps {
    sentence: string;
    word: string;
    onClose: () => void;
    cueStart: number;
    cueEnd: number;
    videoFile: File | null;
    videoUrl?: string;
}

/*dict_api*/

/**
 * The shape of a single sense withing a JMEntry
 */
export interface WordSense {
    order: number;
    pos: string;
    gloss: string;
}

/**
 * The shape of a JMEntry.
 */
export interface JMEntry {
    rank: number;
    kana: string[];
    kanji: string[];
    senses: WordSense[];
}

/**
 * The shape of a JMNEntry.
 */
export interface JMNEntry {
    kana: string[];
    kanji: string[];
    translation_type: string;
    gloss: string[];
}

/**
 * The shape of a KANJIDIC2 entry
 */
export interface KanjiInfo {
    literal: string;
    grade?: number;
    stroke_count: number;
    meanings: string[];
    onyomi: string[];
    kunyomi: string[];
    jlpt_kanjidic?: number;
    jlpt_tanos?: number;
}

/* Server tokenizer */

/**
 * A morphological token from the server tokenizer (fugashi / UniDic).
 *
 * Keys match the API's serialized aliases (FastAPI emits the response model
 * by alias): e.g. `kana` is the katakana reading and `pos1` the top-level
 * part of speech.
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
 * Dictionary data for a single query (replaces `DictLookup`/`DictWildcardLookup`
 * in the new contract; `query` replaces the old `word`/`pattern`).
 */
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
 * A useful word stitched from one or more UniDic short-unit tokens, as
 * returned by `GET /dict/tokenize`.
 *
 * `surface`/`reading` are the component pieces joined; `lemma` is the
 * dictionary-lookup form; `tokens` keeps the original short units.
 */
export interface JapaneseWord {
    surface: string;
    reading: string;
    lemma: string;
    pos: string;
    tokens: Token[];
}

/**
 * A `JapaneseWord` paired with its dictionary data, as returned by
 * `GET /dict/analyze`.
 */
export interface EnrichedJapaneseWord {
    word: JapaneseWord;
    kotobase_data: KotobaseData;
}

/*TranscribePage*/

/**
 * The shape of a message in the transcribe page.
 */
export interface Message {
    id: string;
    type: "user" | "bot";
    text?: string;
    tokens?: IpadicFeatures[];
    rawText?: string;
    audioUrl?: string;
    loading?: boolean;
    isAudioMessage?: boolean;
    isExplanation?: boolean;
    isTranscription?: boolean;
}

/**
 * The props for the ChatBubble component.
 */
export interface ChatBubbleProps {
    msg: Message;
    tokenizer: Tokenizer<IpadicFeatures> | null;
    onWordClick: (sentence: string, word: string) => void;
}

/**
 * The shape of the response from the transcribe endpoint.
 */
export interface TranscriptionResponse {
    transcript: string;
    gpt_explanation?: string;
}

/*SubtitleSettingsContext*/

/**
 * The shape of the subtitle style settings.
 */
export interface SubtitleStyle {
    fontSize: number;
    fontColor: string;
    backgroundColor: string;
    backgroundOpacity: number;
    textShadow: string;
    position: number;
}

/*api*/

/**
 * An error class for API errors.
 *
 * `code` is the server's machine-readable identifier from the error envelope
 * (`{ success: false, error: { code, message, details } }`), when present.
 */
export class ApiError extends Error {
    constructor(
        public status: number,
        message: string,
        public code?: string,
        public details?: unknown
    ) {
        super(message);
    }
}
