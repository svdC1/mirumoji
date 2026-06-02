/**
 * @packageDocumentation Saved-clip types.
 */

import type { EnrichedJapaneseWord } from "@/shared/dict/types";

/**
 * The breakdown payload stored with a saved clip: the focused word + its
 * explanation + the sentence it came from (the Anki export reads all three).
 */
export interface ClipBreakdown {
    focus: EnrichedJapaneseWord | null;
    explanation: string;
    sentence: string;
}

/** A saved clip (`/profiles/clips`). */
export interface Clip {
    id: string;
    file_id: string;
    clip_url: string;
    start_time: number;
    end_time: number;
    breakdown: ClipBreakdown;
}

/** Response from the clip-save endpoint. */
export interface SaveClipResponse {
    clip_id: string;
    file_id: string;
    clip_url: string;
}
