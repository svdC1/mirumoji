/**
 * @packageDocumentation This component is the text analyzer page of the application.
 * It tokenizes pasted Japanese text on the server and displays it as clickable
 * tokens with furigana; clicking a token opens its WordDialog.
 */
import React, { useState } from "react";
import { apiTokenize } from "../services/dictApi";
import { toastApiError } from "../utils/apiErrorToaster";
import WordDialog from "../components/WordDialog";
import TokenizedText from "../components/TokenizedText";
import { JapaneseWord } from "../types/types";

/**
 * The TextPage component.
 *
 * @returns {JSX.Element} The TextPage component.
 */
const TextPage: React.FC = () => {
    const [text, setText] = useState("");
    const [words, setWords] = useState<JapaneseWord[]>([]);
    const [selected, setSelected] = useState<{ sentence: string; word: string } | null>(null);
    const [loading, setLoading] = useState(false);
    const [showFurigana, setShowFurigana] = useState<boolean>(true);
    const [isReadingMode, setIsReadingMode] = useState<boolean>(false);

    const handleRead = async () => {
        if (text.trim() === "" || loading) return;
        setLoading(true);
        try {
            setWords(await apiTokenize(text));
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
                            <TokenizedText
                                words={words}
                                sentence={text}
                                showFurigana={showFurigana}
                                onWordClick={(sentence, word) => setSelected({ sentence, word })}
                                selectedLemma={selected?.word}
                            />
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
                        <div className="mt-4 flex justify-between">
                            <button
                                onClick={handlePaste}
                                className="px-4 py-2 rounded-md font-semibold transition-colors text-sm bg-gray-600 hover:bg-gray-500 text-white"
                            >
                                Paste from Clipboard
                            </button>
                            <button
                                onClick={handleRead}
                                className="px-4 py-2 rounded-md font-semibold transition-colors text-sm bg-indigo-600 hover:bg-indigo-500 text-white disabled:opacity-50"
                                disabled={!text.trim() || loading}
                            >
                                {loading ? "Reading…" : "Read"}
                            </button>
                        </div>
                    </div>
                )}
            </div>
            {selected && (
                <WordDialog
                    sentence={selected.sentence}
                    word={selected.word}
                    onClose={() => setSelected(null)}
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
