/**
 * @packageDocumentation A transcribe-chat message bubble: audio player,
 * tokenized transcript (clickable furigana), or an LLM explanation (markdown).
 */

import ReactMarkdown from "react-markdown";
import remarkBreaks from "remark-breaks";
import remarkGfm from "remark-gfm";
import AudioPlayer from "react-h5-audio-player";
import TokenizedText from "@/shared/components/TokenizedText";
import { cn } from "@/shared/ui";
import type { ChatBubbleProps } from "../types";

/**
 * The ChatBubble component.
 *
 * @param {ChatBubbleProps} props The props.
 * @returns {JSX.Element} The chat bubble.
 */
export default function ChatBubble({ msg, onWordClick }: ChatBubbleProps) {
    const rawSentence = msg.isTranscription && msg.text ? msg.text : "";

    return (
        <div className={cn("flex", msg.type === "user" ? "justify-end" : "justify-start")}>
            <div
                className={cn(
                    "rounded-2xl px-4 py-3 text-sm shadow-soft",
                    msg.isAudioMessage
                        ? "w-full max-w-md sm:max-w-lg md:max-w-2xl"
                        : "w-fit max-w-[90%]",
                    msg.type === "user"
                        ? "bg-shu/90 text-ink"
                        : "border border-ink/10 bg-surface-2 text-ink"
                )}
            >
                {msg.loading && (
                    <div className="animate-pulse italic text-ink-muted">
                        {msg.isAudioMessage
                            ? "Uploading And Transcribing …"
                            : "Generating Explanation …"}
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
                    <span
                        lang="ja"
                        className="mx-auto inline-block max-w-[95%] break-words text-xl sm:text-2xl md:text-3xl"
                    >
                        <TokenizedText
                            words={msg.words}
                            sentence={rawSentence}
                            showFurigana
                            onWordClick={onWordClick}
                        />
                    </span>
                ) : (
                    msg.text && (
                        <ReactMarkdown
                            remarkPlugins={[remarkGfm, remarkBreaks]}
                            className="prose prose-invert prose-sm max-w-prose whitespace-pre-wrap"
                        >
                            {msg.text}
                        </ReactMarkdown>
                    )
                )}
            </div>
        </div>
    );
}
