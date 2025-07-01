/**
 * @fileoverview This file contains functions for querying the dictionary API.
 */

import { apiFetch } from "../services/api";
import { DictLookup } from "../types/types";

/**
 * Queries the dictionary API for a word.
 *
 * @param {string} word The word to query.
 * @returns {Promise<DictLookup>} A promise that resolves to the dictionary lookup data.
 */
export async function apiWordQuery(word: string): Promise<DictLookup> {
    const result = apiFetch<DictLookup>(`/dict/word?word=${word}`, {
        method: "GET",
    });
    return result;
}
