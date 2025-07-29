/**
 * @packageDocumentation This file contains functions for querying the dictionary API.
 */

import { apiFetch } from "../services/api";
import { DictLookup, DictWildcardLookup } from "../types/types";

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

/**
 * Queries the dictionary API for a wildcard pattern.
 *
 * @param {string} pattern The pattern to query.
 * @returns {Promise<DictWildcardLookup>} A promise that resolves to the dictionary wilcard lookup data.
 */
export async function apiWildcardQuery(
    pattern: string
): Promise<DictWildcardLookup> {
    const result = apiFetch<DictWildcardLookup>(
        `/dict/wildcard?pattern=${pattern}`,
        {
            method: "GET",
        }
    );
    return result;
}

/**
 * Filters empty placeholders from a `DictLookup` response object
 * and returns `null` in case the response object is considered empty
 *
 * @param {DictLookup} dictLookup The DictLookup object
 * @returns {DictLookup | null} The filtered object or null
 */
export function filterDictLookup(
    dictLookup: DictLookup | null
): DictLookup | null {
    // Filter Empty Elements
    if (dictLookup) {
        // Empty element has stroke count of `99`
        dictLookup.kanji = dictLookup.kanji.filter(
            (k) => k.stroke_count !== 99
        );
        // Empty element has no `kana` and no `kanji` and one sense with order of `99`
        dictLookup.jmentries = dictLookup.jmentries.filter(
            (jme) =>
                (jme.kanji.length !== 0 || jme.kana.length !== 0) &&
                jme.senses.length !== 0 &&
                jme.senses[0].order !== 99
        );
        // Empty element has no `kana`, `kanji` or `gloss` and empty string as translation type
        dictLookup.jmnentries = dictLookup.jmnentries.filter(
            (jmne) =>
                (jmne.kanji.length !== 0 || jmne.kana.length !== 0) &&
                jmne.gloss.length !== 0 &&
                jmne.translation_type !== ""
        );
    } else {
        return null;
    }
    // Empty response has empty lists and jlpt of `Unknown`
    const empty =
        dictLookup.kanji.length === 0 &&
        dictLookup.jmentries.length === 0 &&
        dictLookup.jmnentries.length === 0 &&
        dictLookup.meanings.length === 0 &&
        dictLookup.examples.length === 0 &&
        dictLookup.jlpt === "Unknown";
    if (!empty) {
        return dictLookup;
    } else {
        return null;
    }
}

/**
 * Filters empty placeholders from a `DictWildcardLookup` response object
 * and returns `null` in case the response object is considered empty
 *
 * @param {DictWildcardLookup} dictLookup The DictWildcardLookup object
 * @returns {DictLookup | null} The filtered object or null
 */
export function filterDictWildcardLookup(
    dictLookup: DictWildcardLookup | null
): DictWildcardLookup | null {
    // Filter Empty Elements
    if (dictLookup) {
        // Empty element has stroke count of `99`
        dictLookup.kanji = dictLookup.kanji.filter(
            (k) => k.stroke_count !== 99
        );
        // Empty element has no `kana` and no `kanji` and one sense with order of `99`
        dictLookup.jmentries = dictLookup.jmentries.filter(
            (jme) =>
                (jme.kanji.length !== 0 || jme.kana.length !== 0) &&
                jme.senses.length !== 0 &&
                jme.senses[0].order !== 99
        );
        // Empty element has no `kana`, `kanji` or `gloss` and empty string as translation type
        dictLookup.jmnentries = dictLookup.jmnentries.filter(
            (jmne) =>
                (jmne.kanji.length !== 0 || jmne.kana.length !== 0) &&
                jmne.gloss.length !== 0 &&
                jmne.translation_type !== ""
        );
    } else {
        return null;
    }
    // Empty response has empty lists and jlpt of `Unknown`
    const empty =
        dictLookup.kanji.length === 0 &&
        dictLookup.jmentries.length === 0 &&
        dictLookup.jmnentries.length === 0 &&
        dictLookup.examples.length === 0;
    if (!empty) {
        return dictLookup;
    } else {
        return null;
    }
}
