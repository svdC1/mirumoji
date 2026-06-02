/**
 * @packageDocumentation This file contains all the type definitions for the application.
 */

/* UserPage*/

/**
 * The shape of a profile's LLM template (`/profiles/template`).
 *
 * `model` is a `provider:model` selector (e.g. `"openai:gpt-4.1-mini"`).
 */
export interface LlmTemplate {
    id: string;
    sys_msg: string;
    prompt: string;
    model: string;
}

/**
 * Availability of an LLM provider, as reported by `/llm/providers`.
 */
export interface ProviderStatus {
    provider: string;
    available: boolean;
}

/**
 * The shape of a profile file (`/profiles/files`).
 */
export type ProfileFile = {
    id: string;
    name: string;
    url: string;
    type: string | null;
    created_at?: string | null;
};

/**
 * The shape of a profile transcript (`/profiles/transcripts`).
 */
export type ProfileTranscript = {
    id: string;
    file_id: string;
    text: string;
    llm_explanation?: string | null;
    url?: string | null;
    created_at?: string | null;
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
 * The shape of the response from the `/video/generate_srt` endpoint.
 */
export interface GenerateSrtResponse {
    file_id: string;
    srt_content: string;
    srt_url: string;
}

/**
 * The shape of the response from the `/video/convert_to_mp4` endpoint.
 */
export interface ConvertVideoResponse {
    converted_video_url: string;
}

/* Dictionary models (kotobase / fugashi) */

/**
 * The shape of a single sense within a JMEntry
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
    grade?: number | null;
    stroke_count?: number | null;
    meanings: string[];
    onyomi: string[];
    kunyomi: string[];
    jlpt_kanjidic?: number | null;
    jlpt_tanos?: number | null;
}

/**
 * Dictionary data for a single query (`/dict/query`), keyed by `query`.
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
 * A morphological token from the server tokenizer (fugashi / UniDic). Keys
 * match the API's serialized aliases (e.g. `kana` is the katakana reading).
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
 * `GET /dict/analyze` and carried as the `focus` of a breakdown.
 */
export interface EnrichedJapaneseWord {
    word: JapaneseWord;
    kotobase_data: KotobaseData;
}

/* LLM (breakdown / explanation) */

/**
 * The response from `/llm/breakdown`: the focused word (with dictionary data)
 * and its explanation within the sentence.
 */
export interface BreakdownResponse {
    focus: EnrichedJapaneseWord | null;
    explanation: string;
}

/**
 * The response from `/llm/explain_sentence`.
 */
export interface ExplanationResponse {
    explanation: string;
}

/**
 * The breakdown payload stored with a saved clip: a {@link BreakdownResponse}
 * plus the sentence it came from (used by the Anki export).
 */
export interface ClipBreakdown {
    focus: EnrichedJapaneseWord | null;
    explanation: string;
    sentence: string;
}

/* SavedPage*/

/**
 * The shape of a saved clip (`/profiles/clips`).
 */
export type Clip = {
    id: string;
    file_id: string;
    clip_url: string;
    start_time: number;
    end_time: number;
    breakdown: ClipBreakdown;
};

/**
 * The shape of the response from the clip-save endpoint.
 */
export interface SaveClipResponse {
    clip_id: string;
    file_id: string;
    clip_url: string;
}

/**
 * The shape of the response from the Anki export endpoint.
 */
export interface AnkiExportResponse {
    anki_deck_url: string;
}

/*SubtitlePlayer */

/**
 * The shape of a subtitle cue. `words` is populated lazily (server tokenizer)
 * when the cue becomes active.
 */
export interface Cue {
    start: number;
    end: number;
    raw: string;
    words?: JapaneseWord[];
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

/* TokenizedText */

/**
 * The props for the TokenizedText component, which renders a list of stitched
 * words as clickable tokens with optional furigana.
 */
export interface TokenizedTextProps {
    words: JapaneseWord[];
    sentence: string;
    showFurigana: boolean;
    onWordClick: (sentence: string, word: string) => void;
    selectedLemma?: string | null;
}

/*TranscribePage*/

/**
 * The shape of a message in the transcribe page.
 */
export interface Message {
    id: string;
    type: "user" | "bot";
    text?: string;
    words?: JapaneseWord[];
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
    onWordClick: (sentence: string, word: string) => void;
}

/**
 * The shape of the response from the `/audio/transcribe` endpoint.
 */
export interface AudioTranscriptResponse {
    transcript_id: string;
    transcript: string;
    original_file_name: string;
    audio_url: string;
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
