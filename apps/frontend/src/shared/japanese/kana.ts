/**
 * @packageDocumentation Japanese character helpers.
 */

/**
 * Whether a character is a (common CJK) Kanji.
 *
 * @param {string} char The character to test.
 * @returns {boolean} `true` for U+4E00–U+9FAF.
 */
export const isKanji = (char: string): boolean => char >= "一" && char <= "龯";

/**
 * Converts Katakana to Hiragana (used to render readings as furigana).
 *
 * @param {string} text The text to convert.
 * @returns {string} The Hiragana form.
 */
export const toHiragana = (text: string): string =>
    text.replace(/[ァ-ヶ]/g, (m) => String.fromCharCode(m.charCodeAt(0) - 0x60));
