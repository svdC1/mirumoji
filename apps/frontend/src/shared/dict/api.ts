/**
 * @packageDocumentation Dictionary + tokenizer API helpers.
 */

import { apiFetch } from "@/shared/api/client";
import type {
    BundleMode,
    Example,
    JMEntry,
    JapaneseWord,
    KanjiAudio,
    KanjiInfo,
    KotobaseData,
    RadicalInfo,
} from "./types";

/**
 * Tokenizes a sentence on the server, returning one stitched `JapaneseWord` per
 * word (no dictionary data).
 *
 * @param {string} sentence The Japanese sentence.
 * @param {BundleMode} [mode="grammar"] How aggressively to group tokens.
 * @returns {Promise<JapaneseWord[]>} The stitched words.
 */
export async function apiTokenize(
    sentence: string,
    mode: BundleMode = "grammar"
): Promise<JapaneseWord[]> {
    const params = new URLSearchParams({ sentence, mode });
    return apiFetch<JapaneseWord[]>(`dict/tokenize?${params.toString()}`, {
        method: "GET",
    });
}

/**
 * Tokenizes many sentences in one request (used to pre-tokenize a whole
 * subtitle file).
 *
 * @param {string[]} sentences The sentences, in order.
 * @param {BundleMode} [mode="grammar"] How aggressively to group tokens.
 * @returns {Promise<JapaneseWord[][]>} One word list per input sentence.
 */
export async function apiTokenizeBatch(
    sentences: string[],
    mode: BundleMode = "grammar"
): Promise<JapaneseWord[][]> {
    return apiFetch<JapaneseWord[][]>("dict/tokenize", {
        method: "POST",
        body: JSON.stringify({ sentences, mode }),
    });
}

/**
 * Looks up dictionary data for a word or wildcard pattern. Optional token
 * hints (reading + part of speech, from tokenization) rank matching entries
 * first and let unknown written forms fall back to a lookup by reading.
 *
 * @param {string} word The word or wildcard pattern.
 * @param {boolean} [wildcard=false] Treat `word` as a wildcard pattern.
 * @param {{ reading?: string; pos?: string }} [hints] Token hints, when known.
 * @returns {Promise<KotobaseData>} The lookup result.
 */
export async function apiDictQuery(
    word: string,
    wildcard = false,
    hints?: { reading?: string; pos?: string }
): Promise<KotobaseData> {
    const params = new URLSearchParams({ word, wildcard: String(wildcard) });
    if (hints?.reading) params.set("reading", hints.reading);
    if (hints?.pos) params.set("pos", hints.pos);
    return apiFetch<KotobaseData>(`dict/query?${params.toString()}`, { method: "GET" });
}

/**
 * Whether a dictionary lookup found nothing (every result list empty).
 *
 * @param {KotobaseData} data The lookup result.
 * @returns {boolean} `true` when empty.
 */
export function isEmptyDict(data: KotobaseData): boolean {
    return (
        data.jmentries.length === 0 &&
        data.jmnentries.length === 0 &&
        data.kanji.length === 0 &&
        data.meanings.length === 0 &&
        data.examples.length === 0
    );
}

/**
 * Fetches the full profile of a single kanji.
 *
 * @param {string} literal The kanji character.
 * @returns {Promise<KanjiInfo>} The kanji profile.
 */
export async function apiKanji(literal: string): Promise<KanjiInfo> {
    const params = new URLSearchParams({ literal });
    return apiFetch<KanjiInfo>(`dict/kanji?${params.toString()}`, { method: "GET" });
}

/**
 * Fetches a kanji's stroke-order diagram as an inline-able SVG document
 * (KanjiVG). Rejects with a 404 `ApiError` when no stroke data exists.
 *
 * @param {string} literal The kanji character.
 * @returns {Promise<string>} The SVG markup.
 */
export async function apiKanjiStrokes(literal: string): Promise<string> {
    const params = new URLSearchParams({ literal });
    const blob = await apiFetch<Blob>(`dict/kanji/strokes?${params.toString()}`, {
        method: "GET",
    });
    return blob.text();
}

/**
 * Lists the pronunciation clips available for a kanji (Kanji Alive).
 *
 * @param {string} literal The kanji character.
 * @returns {Promise<KanjiAudio>} The clip listing (empty without the audio pack).
 */
export async function apiKanjiAudio(literal: string): Promise<KanjiAudio> {
    const params = new URLSearchParams({ literal });
    return apiFetch<KanjiAudio>(`dict/kanji/audio?${params.toString()}`, {
        method: "GET",
    });
}

/**
 * Builds the playable URL of one pronunciation clip, for use as an
 * `<audio>` source (the dictionary endpoints are not profile-scoped).
 *
 * @param {string} literal The kanji character the clip belongs to.
 * @param {string} clip The clip id from {@link apiKanjiAudio}.
 * @returns {string} The clip URL.
 */
export function dictAudioClipUrl(literal: string, clip: string): string {
    const params = new URLSearchParams({ literal, clip });
    return `/api/dict/kanji/audio/clip?${params.toString()}`;
}

/**
 * Lists dictionary entries whose written form uses a kanji.
 *
 * @param {string} literal The kanji character.
 * @param {number} [limit=50] Maximum entries to return.
 * @returns {Promise<JMEntry[]>} The matching entries.
 */
export async function apiKanjiWords(literal: string, limit = 50): Promise<JMEntry[]> {
    const params = new URLSearchParams({ literal, limit: String(limit) });
    return apiFetch<JMEntry[]>(`dict/kanji/words?${params.toString()}`, { method: "GET" });
}

/**
 * Lists example sentences that contain a kanji.
 *
 * @param {string} literal The kanji character.
 * @param {number} [limit=10] Maximum sentences to return.
 * @returns {Promise<Example[]>} The matching sentences with translations.
 */
export async function apiKanjiSentences(literal: string, limit = 10): Promise<Example[]> {
    const params = new URLSearchParams({ literal, limit: String(limit) });
    return apiFetch<Example[]>(`dict/kanji/sentences?${params.toString()}`, { method: "GET" });
}

/**
 * Searches dictionary entries by English meaning (reverse lookup).
 *
 * @param {string} q The English search text.
 * @param {number} [limit=50] Maximum entries to return.
 * @returns {Promise<JMEntry[]>} The matching entries.
 */
export async function apiSearchEnglish(q: string, limit = 50): Promise<JMEntry[]> {
    const params = new URLSearchParams({ q, limit: String(limit) });
    return apiFetch<JMEntry[]>(`dict/search?${params.toString()}`, { method: "GET" });
}

/**
 * Resolves a sense cross-reference or antonym code into its entries.
 *
 * @param {string} ref The reference code from a sense's `xrefs`/`antonyms`.
 * @returns {Promise<JMEntry[]>} The referenced entries.
 */
export async function apiResolveRef(ref: string): Promise<JMEntry[]> {
    const params = new URLSearchParams({ ref });
    return apiFetch<JMEntry[]>(`dict/resolve?${params.toString()}`, { method: "GET" });
}

/**
 * Lists every search radical with its stroke count (RADKFILE).
 *
 * @returns {Promise<RadicalInfo[]>} All search radicals.
 */
export async function apiRadicals(): Promise<RadicalInfo[]> {
    return apiFetch<RadicalInfo[]>("dict/radicals", { method: "GET" });
}

/**
 * Finds kanji by their radical components.
 *
 * @param {string[]} radicals The radical glyphs.
 * @param {"all" | "any"} [mode="all"] Whether a kanji must contain every
 *     picked radical or at least one of them.
 * @returns {Promise<KanjiInfo[]>} The matching kanji.
 */
export async function apiByRadicals(
    radicals: string[],
    mode: "all" | "any" = "all"
): Promise<KanjiInfo[]> {
    const params = new URLSearchParams({ radicals: radicals.join(","), mode });
    return apiFetch<KanjiInfo[]>(`dict/by-radicals?${params.toString()}`, { method: "GET" });
}
