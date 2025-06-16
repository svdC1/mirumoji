// Helper function to check for Kanji characters
export const isKanji = (char: string): boolean => {
    // Unicode range for Kanji characters (common CJK Unified Ideographs)
    // This range covers most common Kanji but might not be exhaustive for all possible Kanji.
    return char >= "\u4e00" && char <= "\u9faf";
};

// Helper function to convert Katakana to Hiragana
export const toHiragana = (text: string): string => {
    return text.replace(/[\u30a1-\u30f6]/g, (match) => {
        return String.fromCharCode(match.charCodeAt(0) - 0x60);
    });
};
