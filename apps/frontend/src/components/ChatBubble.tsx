/**
 * @packageDocumentation This component displays a chat bubble.
 */

import ReactMarkdown from "react-markdown";
import remarkBreaks from "remark-breaks";
import remarkGfm from "remark-gfm";
import type { ChatBubbleProps } from "@/features/transcribe/types";
import TokenizedText from "@/shared/components/TokenizedText";
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
const ChatBubble = ({ msg, onWordClick }: ChatBubbleProps) => {
    const containerClass = msg.isAudioMessage
        ? "w-full max-w-md sm:max-w-lg md:max-w-2xl"
        : "w-fit max-w-[90%]";
    const bubbleColor = msg.type === "user" ? "bg-indigo-600 ml-auto" : "bg-zinc-800 mr-auto";
    const rawSentence = msg.isTranscription && msg.text ? msg.text : "";

    return (
        <div className={`flex ${msg.type === "user" ? "justify-end" : "justify-start"}`}>
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
                {msg.words && msg.words.length > 0 ? (
                    <span className="inline-block mx-auto max-w-[95%] break-words text-xl sm:text-2xl md:text-3xl lg:text-4xl">
                        <TokenizedText
                            words={msg.words}
                            sentence={rawSentence}
                            showFurigana={true}
                            onWordClick={onWordClick}
                        />
                    </span>
                ) : (
                    msg.text && (
                        <ReactMarkdown
                            remarkPlugins={[remarkGfm, remarkBreaks]}
                            className={"prose text-sm max-w-prose whitespace-pre-wrap"}
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
