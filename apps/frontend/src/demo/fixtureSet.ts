/**
 * @packageDocumentation The allowlist of dictionary entries captured in the demo
 * fixtures, so demo views can disable links whose target has no fixture (rather
 * than let a click land on an empty "Nothing Found" page).
 */

import inset from "./generated/inset.json";

const { words, kanji } = inset as unknown as { words: string[]; kanji: string[] };
const wordSet = new Set(words);
const kanjiSet = new Set(kanji);

/** Whether a word / wildcard term has a captured dictionary fixture. */
export function hasWord(term: string): boolean {
    return wordSet.has(term);
}

/** Whether a kanji literal has a captured dictionary fixture. */
export function hasKanji(literal: string): boolean {
    return kanjiSet.has(literal);
}
