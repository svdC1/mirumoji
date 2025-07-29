/**
 * @packageDocumentation This component is the text analyzer page of the application.
 * It allows the user to input a text and have it tokenized and displayed with furigana.
 * The user can then click on the tokens to get more information about them.
 */
import React, { useState, useEffect } from "react";
import {
    getTokenizer,
    IpadicFeatures,
    KuromojiTokenizer,
} from "../services/tokenizer";
import WordDialog from "../components/WordDialog";
import { isKanji, toHiragana } from "../utils/languageUtils";

/**
 * The TextPage component.
 *
 * This component is responsible for the following:
 * - Allowing the user to input a text.
 * - Tokenizing the text and displaying it as a series of clickable tokens.
 * - Displaying furigana above the tokens.
 * - Allowing the user to toggle the visibility of the furigana.
 * - Displaying a dialog with more information about a token when it is clicked.
 *
 * @returns {JSX.Element} The TextPage component.
 */
const TextPage: React.FC = () => {
    const [text, setText] = useState("");
    const [tokens, setTokens] = useState<IpadicFeatures[]>([]);
    const [selectedToken, setSelectedToken] = useState<IpadicFeatures | null>(
        null
    );
    const [tokenizer, setTokenizer] = useState<KuromojiTokenizer | null>(null);
    const [showFurigana, setShowFurigana] = useState<boolean>(true);
    const [isReadingMode, setIsReadingMode] = useState<boolean>(false);

    useEffect(() => {
        getTokenizer().then(setTokenizer);
    }, []);

    const handleRead = () => {
        if (tokenizer && text.trim() !== "") {
            const tokenizedText = tokenizer.tokenize(text);
            setTokens(tokenizedText);
            setIsReadingMode(true);
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

    const handleTextChange = (
        event: React.ChangeEvent<HTMLTextAreaElement>
    ) => {
        setText(event.target.value);
    };

    const handleWordClick = (token: IpadicFeatures) => {
        setSelectedToken(token);
    };

    const handleCloseDialog = () => {
        setSelectedToken(null);
    };

    return (
        <div className="p-4 bg-gray-900 text-white min-h-screen">
            <div className="max-w-4xl mx-auto">
                <h1 className="text-3xl font-bold mb-4 text-center">
                    Text Analyzer
                </h1>

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
                                {showFurigana
                                    ? "Hide Furigana"
                                    : "Show Furigana"}
                            </button>
                        </div>
                        <div className="p-4 bg-gray-800 rounded-lg text-2xl leading-loose">
                            {tokens.map((token, index) => {
                                const shouldDisplayFurigana =
                                    showFurigana &&
                                    token.reading &&
                                    token.surface_form !== token.reading &&
                                    token.surface_form.split("").some(isKanji);
                                const furiganaText = shouldDisplayFurigana
                                    ? toHiragana(token.reading!)
                                    : null;

                                return (
                                    <button
                                        key={index}
                                        className="inline-flex flex-col items-center mx-1 group align-bottom"
                                        onClick={() => handleWordClick(token)}
                                    >
                                        {furiganaText && (
                                            <span className="text-xs text-gray-400 group-hover:text-yellow-300">
                                                {furiganaText}
                                            </span>
                                        )}
                                        <span
                                            className={`underline ${
                                                selectedToken === token
                                                    ? "text-yellow-400"
                                                    : "group-hover:text-yellow-300"
                                            }`}
                                        >
                                            {token.surface_form}
                                        </span>
                                    </button>
                                );
                            })}
                        </div>
                    </div>
                ) : (
                    <div>
                        <textarea
                            className="w-full h-96 p-4 border border-gray-600 rounded-lg bg-gray-800 text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
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
                                disabled={!text.trim()}
                            >
                                Read
                            </button>
                        </div>
                    </div>
                )}
            </div>
            {selectedToken && (
                <WordDialog
                    sentence={text}
                    word={selectedToken.surface_form}
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
