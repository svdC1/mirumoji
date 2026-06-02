/**
 * @packageDocumentation Renders a list of stitched `JapaneseWord`s as clickable
 * tokens with optional furigana. Shared by the text analyzer, the subtitle
 * player, and the transcribe chat so they all use the server tokenizer the
 * same way. Font size is inherited from the parent container.
 */

import { TokenizedTextProps } from "../types/types";
import { isKanji, toHiragana } from "../utils/languageUtils";

/**
 * The TokenizedText component.
 *
 * @param {TokenizedTextProps} props The props for the component.
 * @returns {JSX.Element} The rendered clickable tokens.
 */
export default function TokenizedText({
    words,
    sentence,
    showFurigana,
    onWordClick,
    selectedLemma,
}: TokenizedTextProps) {
    return (
        <>
            {words.map((word, i) => {
                const hasFurigana =
                    showFurigana && !!word.reading && word.surface.split("").some(isKanji);
                const furigana = hasFurigana ? toHiragana(word.reading) : null;

                return (
                    <button
                        key={i}
                        className="inline-flex flex-col items-center mx-1 group align-bottom"
                        onClick={() => onWordClick(sentence, word.lemma)}
                    >
                        {furigana && (
                            <span className="text-xs text-gray-400 group-hover:text-yellow-300">
                                {furigana}
                            </span>
                        )}
                        <span
                            className={`underline ${
                                selectedLemma === word.lemma
                                    ? "text-yellow-400"
                                    : "group-hover:text-yellow-300"
                            }`}
                        >
                            {word.surface}
                        </span>
                    </button>
                );
            })}
        </>
    );
}
