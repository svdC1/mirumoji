/**
 * @packageDocumentation Transcribe feature types.
 */

import type { JapaneseWord } from "@/shared/dict/types";

/** A message in the transcribe chat. */
export interface Message {
    id: string;
    type: "user" | "bot";
    text?: string;
    words?: JapaneseWord[];
    audioUrl?: string;
    loading?: boolean;
    isAudioMessage?: boolean;
    isTranscription?: boolean;
}

/** Props for the ChatBubble component. */
export interface ChatBubbleProps {
    msg: Message;
    onWordClick: (sentence: string, word: string) => void;
}

/** Response from `/audio/transcribe`. */
export interface AudioTranscriptResponse {
    transcript_id: string;
    transcript: string;
    original_file_name: string;
    audio_url: string;
}
