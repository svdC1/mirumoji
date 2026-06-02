/**
 * @packageDocumentation Player feature types.
 */

import type { JapaneseWord } from "@/shared/dict/types";

/**
 * A subtitle cue. `words` is the pre-tokenized form (server tokenizer),
 * populated once the SRT is parsed.
 */
export interface Cue {
    start: number;
    end: number;
    raw: string;
    words?: JapaneseWord[];
}

/** Props for the SubtitlePlayer / video stage. */
export interface SubtitlePlayerProps {
    video: File;
    videoUrl?: string;
    srt: File | null;
    showFurigana: boolean;
}

/** Props for the settings drawer / load controls. */
export interface SettingsDrawerProps {
    video: File | null;
    srt: File | null;
    onVideo: (file: File | null) => void;
    onVideoUrl?: (url: string) => void;
    onSrt: (file: File | null) => void;
    onClose: () => void;
    showFurigana: boolean;
    onToggleFurigana: () => void;
}

/** Response from `/video/generate_srt`. */
export interface GenerateSrtResponse {
    file_id: string;
    srt_content: string;
    srt_url: string;
}

/** Response from `/video/convert_to_mp4`. */
export interface ConvertVideoResponse {
    converted_video_url: string;
}
