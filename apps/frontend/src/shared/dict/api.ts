/**
 * @packageDocumentation Dictionary + tokenizer API helpers.
 */

import { apiFetch } from "@/shared/api/client";
import type { BundleMode, JapaneseWord, KotobaseData } from "./types";

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
 * Looks up dictionary data for a word or wildcard pattern.
 *
 * @param {string} word The word or wildcard pattern.
 * @param {boolean} [wildcard=false] Treat `word` as a wildcard pattern.
 * @returns {Promise<KotobaseData>} The lookup result.
 */
export async function apiDictQuery(word: string, wildcard = false): Promise<KotobaseData> {
    const params = new URLSearchParams({ word, wildcard: String(wildcard) });
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
