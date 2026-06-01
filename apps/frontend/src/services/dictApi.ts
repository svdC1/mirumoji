/**
 * @packageDocumentation This file contains functions for querying the dictionary API.
 */

import { apiFetch } from "../services/api";
import { JapaneseWord, KotobaseData } from "../types/types";

/**
 * Tokenizes a Japanese sentence on the server (fugashi / UniDic), returning
 * one stitched `JapaneseWord` per word (no dictionary data).
 *
 * @param {string} sentence The Japanese sentence to tokenize.
 * @returns {Promise<JapaneseWord[]>} A promise that resolves to the words.
 */
export async function apiTokenize(sentence: string): Promise<JapaneseWord[]> {
    return apiFetch<JapaneseWord[]>(`dict/tokenize?sentence=${encodeURIComponent(sentence)}`, {
        method: "GET",
    });
}

/**
 * Looks up dictionary data for a single word or a wildcard pattern.
 *
 * @param {string} word The word or wildcard pattern to look up.
 * @param {boolean} [wildcard=false] Treat `word` as a wildcard pattern.
 * @returns {Promise<KotobaseData>} A promise that resolves to the lookup data.
 */
export async function apiDictQuery(word: string, wildcard = false): Promise<KotobaseData> {
    const params = new URLSearchParams({
        word,
        wildcard: String(wildcard),
    });
    return apiFetch<KotobaseData>(`dict/query?${params.toString()}`, {
        method: "GET",
    });
}

/**
 * Whether a dictionary lookup found nothing.
 *
 * The server returns clean, never-null collections, so "empty" is simply every
 * result list being empty (no placeholder filtering needed).
 *
 * @param {KotobaseData} data The dictionary lookup data.
 * @returns {boolean} `true` when there are no entries, kanji, meanings, or
 *     examples.
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
