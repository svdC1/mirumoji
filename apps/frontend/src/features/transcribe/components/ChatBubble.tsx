/**
 * @packageDocumentation A transcribe-chat message: the audio renders as the
 * themed AudioPlayer; a transcript renders as clickable furigana tokens; an LLM
 * explanation renders as markdown — each in an aligned bubble.
 */

import ReactMarkdown from "react-markdown";
import remarkBreaks from "remark-breaks";
import remarkGfm from "remark-gfm";
import TokenizedText from "@/shared/components/TokenizedText";
import { ExplanationSkeleton } from "@/shared/components/ExplanationSkeleton";
import { AudioPlayer, cn } from "@/shared/ui";
import type { ChatBubbleProps } from "../types";

/**
 * The ChatBubble component.
 *
 * @param {ChatBubbleProps} props The props.
 * @returns {JSX.Element} The chat bubble.
 */
export default function ChatBubble({ msg, onWordClick }: ChatBubbleProps) {
    const isUser = msg.type === "user";

    // The uploaded/recorded audio renders as the standalone themed player.
    if (msg.audioUrl) {
        return (
            <div className="flex justify-end">
                <AudioPlayer src={msg.audioUrl} className="w-full max-w-md sm:max-w-lg" />
            </div>
        );
    }

    const rawSentence = msg.isTranscription && msg.text ? msg.text : "";

    return (
        <div className={cn("flex", isUser ? "justify-end" : "justify-start")}>
            <div
                className={cn(
                    "max-w-[85%] rounded-2xl px-4 py-3 text-sm shadow-soft",
                    isUser ? "bg-shu/90 text-ink" : "border border-ink/10 bg-surface text-ink"
                )}
            >
                {msg.loading ? (
                    <span className="animate-pulse italic text-ink-muted">
                        {msg.isAudioMessage
                            ? "Uploading And Transcribing ..."
                            : "Generating Explanation ..."}
                    </span>
                ) : msg.words && msg.words.length > 0 ? (
                    <p lang="ja" className="text-lg leading-relaxed sm:text-xl">
                        <TokenizedText
                            words={msg.words}
                            sentence={rawSentence}
                            showFurigana
                            onWordClick={onWordClick}
                        />
                    </p>
                ) : msg.text ? (
                    <ReactMarkdown
                        remarkPlugins={[remarkGfm, remarkBreaks]}
                        className="prose prose-invert prose-sm max-w-none whitespace-pre-wrap"
                    >
                        {msg.text}
                    </ReactMarkdown>
                ) : (
                    // A streamed explanation arrives empty, then fills in. Until
                    // the first token, show the same skeleton as the word dialog
                    // rather than an empty bubble. Fixed width so the bubble
                    // (which sizes to its content) doesn't collapse.
                    <div className="w-48">
                        <ExplanationSkeleton />
                    </div>
                )}
            </div>
        </div>
    );
}
