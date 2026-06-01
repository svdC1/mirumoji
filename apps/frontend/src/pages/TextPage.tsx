/**
 * @packageDocumentation This component is the text analyzer page of the application.
 * It allows the user to input a text and have it tokenized and displayed with furigana.
 * The user can then click on the tokens to get more information about them.
 *
 * Phase 0: a "Tokenizer" toggle lets the same text be tokenized via the
 * in-browser kuromoji tokenizer or the server `/dict/tokenize` endpoint, so the
 * two can be compared directly before kuromoji is dropped.
 */
import React, { useState, useEffect } from "react";
import { getTokenizer, KuromojiTokenizer } from "../services/tokenizer";
import { apiTokenize } from "../services/dictApi";
import { toastApiError } from "../utils/apiErrorToaster";
import WordDialog from "../components/WordDialog";
import { isKanji, toHiragana } from "../utils/languageUtils";

/** Which tokenizer produced the displayed tokens. */
type TokenizerSource = "kuromoji" | "server";

/** A display-normalized token shared by both tokenizer sources. */
interface DisplayToken {
    /** The surface form as it appears in the text. */
    surface: string;
    /** Katakana reading (may be empty). */
    reading: string;
    /** Dictionary base form used for lookups (falls back to the surface). */
    base: string;
}

/**
 * The TextPage component.
 *
 * Tokenizes pasted Japanese text into clickable tokens with furigana, via
 * either kuromoji (in-browser) or the server tokenizer, and opens a WordDialog
 * for a clicked token.
 *
 * @returns {JSX.Element} The TextPage component.
 */
const TextPage: React.FC = () => {
    const [text, setText] = useState("");
    const [tokens, setTokens] = useState<DisplayToken[]>([]);
    const [selected, setSelected] = useState<DisplayToken | null>(null);
    const [tokenizer, setTokenizer] = useState<KuromojiTokenizer | null>(null);
    const [source, setSource] = useState<TokenizerSource>("kuromoji");
    const [loading, setLoading] = useState(false);
    const [showFurigana, setShowFurigana] = useState<boolean>(true);
    const [isReadingMode, setIsReadingMode] = useState<boolean>(false);

    useEffect(() => {
        getTokenizer().then(setTokenizer);
    }, []);

    const handleRead = async () => {
        if (text.trim() === "" || loading) return;

        if (source === "kuromoji") {
            if (!tokenizer) return;
            const next: DisplayToken[] = tokenizer.tokenize(text).map((t) => ({
                surface: t.surface_form,
                reading: t.reading && t.reading !== "*" ? t.reading : "",
                base: t.basic_form && t.basic_form !== "*" ? t.basic_form : t.surface_form,
            }));
            setTokens(next);
            setIsReadingMode(true);
            return;
        }

        // Server tokenizer
        setLoading(true);
        try {
            const words = await apiTokenize(text);
            const next: DisplayToken[] = words.map((w) => ({
                surface: w.surface,
                reading: w.reading ?? "",
                base: w.lemma || w.surface,
            }));
            setTokens(next);
            setIsReadingMode(true);
        } catch (e) {
            toastApiError(e);
        } finally {
            setLoading(false);
        }
    };

    const handlePaste = async () => {
        try {
            const clipboardText = await navigator.clipboard.readText();
            setText(clipboardText);
        } catch (err) {
            console.error("Failed to read clipboard contents: ", err);
        }
    };

    const handleTextChange = (event: React.ChangeEvent<HTMLTextAreaElement>) => {
        setText(event.target.value);
    };

    const handleCloseDialog = () => {
        setSelected(null);
    };

    return (
        <div className="p-4 bg-gray-900 text-white select-none min-h-screen">
            <div className="max-w-4xl mx-auto">
                <h1 className="text-3xl font-bold mb-4 text-center">Text Analyzer</h1>

                {isReadingMode ? (
                    <div>
                        <div className="flex justify-between mb-4">
                            <button
                                onClick={() => setIsReadingMode(false)}
                                className="px-4 py-2 rounded-md font-semibold transition-colors text-sm bg-gray-600 hover:bg-gray-500 text-white"
                            >
                                &larr; Back to Editor
                            </button>
                            <span className="px-3 py-2 text-xs text-gray-400 self-center">
                                Tokenizer: {source}
                            </span>
                            <button
                                onClick={() => setShowFurigana(!showFurigana)}
                                className={`px-4 py-2 rounded-md font-semibold transition-colors text-sm ${
                                    showFurigana
                                        ? "bg-indigo-600 hover:bg-indigo-500 text-white"
                                        : "bg-gray-700 hover:bg-gray-600 text-gray-300"
                                }`}
                            >
                                {showFurigana ? "Hide Furigana" : "Show Furigana"}
                            </button>
                        </div>
                        <div className="p-4 bg-gray-800 rounded-lg text-2xl leading-loose">
                            {tokens.map((token, index) => {
                                const shouldDisplayFurigana =
                                    showFurigana &&
                                    token.reading &&
                                    token.surface !== token.reading &&
                                    token.surface.split("").some(isKanji);
                                const furiganaText = shouldDisplayFurigana
                                    ? toHiragana(token.reading)
                                    : null;

                                return (
                                    <button
                                        key={index}
                                        className="inline-flex flex-col items-center mx-1 group align-bottom"
                                        onClick={() => setSelected(token)}
                                    >
                                        {furiganaText && (
                                            <span className="text-xs text-gray-400 group-hover:text-yellow-300">
                                                {furiganaText}
                                            </span>
                                        )}
                                        <span
                                            className={`underline ${
                                                selected === token
                                                    ? "text-yellow-400"
                                                    : "group-hover:text-yellow-300"
                                            }`}
                                        >
                                            {token.surface}
                                        </span>
                                    </button>
                                );
                            })}
                        </div>
                    </div>
                ) : (
                    <div>
                        <textarea
                            className="w-full h-96 p-4 border text-center border-gray-600 rounded-lg bg-gray-800 text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                            placeholder="Paste your Japanese text here..."
                            value={text}
                            onChange={handleTextChange}
                        />
                        <div className="mt-4 flex flex-wrap items-center justify-between gap-2">
                            <button
                                onClick={handlePaste}
                                className="px-4 py-2 rounded-md font-semibold transition-colors text-sm bg-gray-600 hover:bg-gray-500 text-white"
                            >
                                Paste from Clipboard
                            </button>

                            {/* Phase 0: tokenizer source toggle for comparison */}
                            <div className="inline-flex rounded-md overflow-hidden border border-gray-600">
                                {(["kuromoji", "server"] as const).map((s) => (
                                    <button
                                        key={s}
                                        onClick={() => setSource(s)}
                                        className={`px-3 py-2 text-sm font-semibold transition-colors ${
                                            source === s
                                                ? "bg-indigo-600 text-white"
                                                : "bg-gray-700 hover:bg-gray-600 text-gray-300"
                                        }`}
                                    >
                                        {s === "kuromoji" ? "kuromoji" : "server"}
                                    </button>
                                ))}
                            </div>

                            <button
                                onClick={handleRead}
                                className="px-4 py-2 rounded-md font-semibold transition-colors text-sm bg-indigo-600 hover:bg-indigo-500 text-white disabled:opacity-50"
                                disabled={
                                    !text.trim() || loading || (source === "kuromoji" && !tokenizer)
                                }
                            >
                                {loading ? "Reading…" : "Read"}
                            </button>
                        </div>
                    </div>
                )}
            </div>
            {selected && (
                <WordDialog
                    sentence={text}
                    word={selected.base}
                    onClose={handleCloseDialog}
                    cueStart={0}
                    cueEnd={0}
                    videoFile={null}
                    videoUrl={undefined}
                />
            )}
        </div>
    );
};

export default TextPage;
