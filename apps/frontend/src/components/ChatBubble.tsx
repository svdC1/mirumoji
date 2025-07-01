/**
 * @fileoverview This component displays a chat bubble.
 */

import ReactMarkdown from "react-markdown";
import remarkBreaks from "remark-breaks";
import { ChatBubbleProps } from "../types/types";
import { isKanji, toHiragana } from "../utils/languageUtils";
import AudioPlayer from "react-h5-audio-player";

/**
 * The ChatBubble component.
 *
 * This component is responsible for the following:
 * - Displaying a chat message.
 * - Displaying an audio player if the message is an audio message.
 * - Displaying a transcription of the audio if the message is a transcription.
 * - Displaying a GPT-powered explanation of the transcription if the message is an explanation.
 *
 * @param {ChatBubbleProps} props The props for the component.
 * @returns {JSX.Element} The ChatBubble component.
 */
const ChatBubble = ({ msg, tokenizer, onWordClick }: ChatBubbleProps) => {
    const containerClass = msg.isAudioMessage
        ? "w-full max-w-md sm:max-w-lg md:max-w-2xl"
        : "w-fit max-w-[90%]";
    const bubbleColor =
        msg.type === "user" ? "bg-indigo-600 ml-auto" : "bg-zinc-800 mr-auto";
    const rawSentence = msg.isTranscription && msg.text ? msg.text : "";

    return (
        <div
            className={`flex ${
                msg.type === "user" ? "justify-end" : "justify-start"
            }`}
        >
            <div
                className={`${containerClass} ${bubbleColor} px-4 py-3 rounded-2xl text-white text-sm shadow-md`}
            >
                {msg.loading && (
                    <div className="italic animate-pulse">
                        {msg.isAudioMessage
                            ? "Uploading and Transcribing…"
                            : "Generating explanation…"}
                    </div>
                )}
                {msg.audioUrl && (
                    <AudioPlayer
                        src={msg.audioUrl}
                        layout="stacked"
                        showJumpControls={false}
                        customAdditionalControls={[]}
                        customVolumeControls={[]}
                        className="mt-2 rounded-md"
                    />
                )}
                {msg.tokens && msg.tokens.length > 0 ? (
                    <span className="inline-block mx-auto max-w-[95%] break-words text-xl sm:text-2xl md:text-3xl lg:text-4xl">
                        {msg.tokens.map((token, i) => {
                            const showFurigana =
                                token.reading &&
                                token.surface_form !== token.reading &&
                                token.surface_form.split("").some(isKanji);
                            const furiganaText = showFurigana
                                ? toHiragana(token.reading!)
                                : null;

                            return (
                                <button
                                    key={i}
                                    className="inline-flex flex-col items-center mx-1 group align-bottom"
                                    onClick={() =>
                                        onWordClick(
                                            rawSentence,
                                            token.surface_form
                                        )
                                    }
                                >
                                    {showFurigana && furiganaText && (
                                        <span className="text-xs text-gray-400 group-hover:text-yellow-300">
                                            {furiganaText}
                                        </span>
                                    )}
                                    <span className="underline group-hover:text-yellow-300">
                                        {token.surface_form}
                                    </span>
                                </button>
                            );
                        })}
                    </span>
                ) : (
                    msg.text && (
                        <ReactMarkdown
                            remarkPlugins={[remarkBreaks]}
                            className={
                                msg.isExplanation
                                    ? "prose dark:prose-invert prose-sm max-w-none border-t border-zinc-700 pt-3 mt-3"
                                    : "prose dark:prose-invert prose-sm max-w-none"
                            }
                        >
                            {msg.text}
                        </ReactMarkdown>
                    )
                )}
            </div>
        </div>
    );
};

export default ChatBubble;
