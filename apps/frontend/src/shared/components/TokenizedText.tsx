/**
 * @packageDocumentation Renders stitched `JapaneseWord`s as clickable tokens
 * with optional furigana. Shared by the text analyzer, subtitle player, and
 * transcribe chat. Font size + color are inherited from the parent (so the
 * subtitle style settings apply); the interaction accent is the theme's
 * vermilion. No blanket underline — affordance is a subtle hover highlight.
 */

import { isKanji, toHiragana } from "@/shared/japanese/kana";
import { cn } from "@/shared/ui";
import type { JapaneseWord } from "@/shared/dict/types";

export interface TokenizedTextProps {
    words: JapaneseWord[];
    sentence: string;
    showFurigana: boolean;
    onWordClick: (sentence: string, word: string) => void;
    selectedLemma?: string | null;
}

/**
 * The TokenizedText component.
 *
 * @param {TokenizedTextProps} props The props.
 * @returns {JSX.Element} The clickable tokens.
 */
export default function TokenizedText({
    words,
    sentence,
    showFurigana,
    onWordClick,
    selectedLemma,
}: TokenizedTextProps) {
    return (
        <span className="inline">
            {words.map((word, i) => {
                const hasFurigana =
                    showFurigana && !!word.reading && word.surface.split("").some(isKanji);
                const furigana = hasFurigana ? toHiragana(word.reading) : null;
                const selected = selectedLemma != null && selectedLemma === word.lemma;

                return (
                    <button
                        key={i}
                        type="button"
                        lang="ja"
                        onClick={() => onWordClick(sentence, word.lemma)}
                        className={cn(
                            "group/token relative inline-flex flex-col items-center rounded-[0.3em] px-[0.15em] align-bottom leading-tight transition-colors",
                            "hover:bg-shu/20 focus:outline-none focus-visible:bg-shu/20",
                            selected && "bg-shu/15"
                        )}
                    >
                        {furigana && (
                            <span
                                aria-hidden
                                className={cn(
                                    "pointer-events-none select-none text-[0.5em] leading-none transition-colors",
                                    selected
                                        ? "text-shu"
                                        : "text-current opacity-55 group-hover/token:text-shu group-hover/token:opacity-100"
                                )}
                            >
                                {furigana}
                            </span>
                        )}
                        <span
                            className={cn(
                                "transition-colors",
                                selected
                                    ? "text-shu"
                                    : "decoration-shu/0 underline-offset-[0.2em] group-hover/token:text-shu"
                            )}
                        >
                            {word.surface}
                        </span>
                    </button>
                );
            })}
        </span>
    );
}
