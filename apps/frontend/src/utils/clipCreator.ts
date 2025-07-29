/**
 * @packageDocumentation Provides a utility for creating and saving video clips.
 * This module orchestrates the recording process, data preparation, and API submission.
 */

import { recordMediaStream } from "./mediaRecorder";
import { apiFetch } from "../services/api";
import { SaveClipResponse, BreakdownData } from "../types/types";
/**
 * Creates and saves a video clip by recording a segment from a video element,
 * bundling it with GPT data, and uploading it to the server.
 *
 * @param {string} videoElementId The ID of the HTMLVideoElement to record from.
 * @param {number} cueStart The start time of the clip in seconds.
 * @param {number} cueEnd The end time of the clip in seconds.
 * @param {any} gptData The GPT breakdown data associated with the clip.
 * @param {(message: string, type: 'success' | 'error' | 'loading') => void} onProgress A callback to report the progress of the operation.
 * @returns {Promise<void>} A promise that resolves when the operation is complete or rejects on error.
 */
export async function createAndSaveClip(
    videoElementId: string,
    cueStart: number,
    cueEnd: number,
    gptData: BreakdownData,
    onProgress: (message: string, type: "success" | "error" | "loading") => void
): Promise<void> {
    // Get Video Element
    const videoElement = document.getElementById(
        videoElementId
    ) as HTMLVideoElement;
    if (!videoElement) {
        onProgress("Video player not found.", "error");
        throw new Error("Video player not found.");
    }

    // Pad cueEnd 1s to catch eventual phrase cuts
    let adjustedCueEnd = cueEnd + 1.0;
    if (cueStart >= adjustedCueEnd) {
        onProgress("Clip start time is after end time.", "error");
        throw new Error("Clip start time is after end time");
    }

    // Avoid cueEnd getting bigger than video duration due to 1s padding.
    const videoDuration = videoElement.duration;
    if (
        typeof videoDuration === "number" &&
        !isNaN(videoDuration) &&
        isFinite(videoDuration)
    ) {
        if (cueStart >= videoDuration) {
            onProgress("Clip start time is at or after video end.", "error");
            throw new Error("Clip start time is at or after video end.");
        }
        if (adjustedCueEnd > videoDuration) {
            adjustedCueEnd = videoDuration;
        }
    } else {
        // When video duration is not availalbe such as streams remove the 1s padding.
        adjustedCueEnd = cueEnd;
    }

    try {
        onProgress("Recording clip...", "loading");
        // Get File
        const clipFile = await recordMediaStream(
            videoElement,
            cueStart,
            adjustedCueEnd
        );

        onProgress("Uploading clip...", "loading");

        // Request API endpoint to save the clip
        const formData = new FormData();
        formData.append("clip_start_time", cueStart.toString());
        formData.append("clip_end_time", adjustedCueEnd.toString());
        formData.append("gpt_breakdown_response", JSON.stringify(gptData));
        formData.append("video_clip", clipFile, clipFile.name);

        const response = await apiFetch<SaveClipResponse>(
            "/profiles/clips/save",
            {
                method: "POST",
                body: formData,
            }
        );

        if (response.success) {
            onProgress(response.message || "Clip saved!", "success");
        } else {
            throw new Error(
                response.message || "Failed to save clip on the server."
            );
        }
    } catch (error: any) {
        console.error("Error during clip saving process:", error);
        onProgress(
            error.message ||
                "An unexpected error occurred while saving the clip.",
            "error"
        );
        throw error; // Re-throw to allow the caller to handle it if needed.
    }
}
