/**
 * @packageDocumentation This file contains utility functions for working with Japanese characters.
 */

/**
 * Checks if a character is a Kanji character.
 *
 * @param {string} char The character to check.
 * @returns {boolean} True if the character is a Kanji character, false otherwise.
 */
export const isKanji = (char: string): boolean => {
    // Unicode range for Kanji characters (common CJK Unified Ideographs)
    // This range covers most common Kanji but might not be exhaustive for all possible Kanji.
    return char >= "\u4e00" && char <= "\u9faf";
};

/**
 * Converts a string from Katakana to Hiragana.
 *
 * @param {string} text The string to convert.
 * @returns {string} The converted string.
 */
export const toHiragana = (text: string): string => {
    return text.replace(/[\u30a1-\u30f6]/g, (match) => {
        return String.fromCharCode(match.charCodeAt(0) - 0x60);
    });
};
