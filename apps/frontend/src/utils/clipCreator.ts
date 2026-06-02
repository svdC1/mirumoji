/**
 * @packageDocumentation Provides a utility for creating and saving video clips.
 * This module orchestrates the recording process, data preparation, and API submission.
 */

import { recordMediaStream } from "./mediaRecorder";
import { uploadFile } from "../services/api";
import { SaveClipResponse, ClipBreakdown } from "../types/types";
/**
 * Creates and saves a video clip by recording a segment from a video element,
 * bundling it with its breakdown data, and uploading it to the server.
 *
 * @param {string} videoElementId The ID of the HTMLVideoElement to record from.
 * @param {number} cueStart The start time of the clip in seconds.
 * @param {number} cueEnd The end time of the clip in seconds.
 * @param {ClipBreakdown} breakdown The breakdown data associated with the clip.
 * @param {(message: string, type: 'success' | 'error' | 'loading') => void} onProgress A callback to report the progress of the operation.
 * @returns {Promise<void>} A promise that resolves when the operation is complete or rejects on error.
 */
export async function createAndSaveClip(
    videoElementId: string,
    cueStart: number,
    cueEnd: number,
    breakdown: ClipBreakdown,
    onProgress: (message: string, type: "success" | "error" | "loading") => void
): Promise<void> {
    // Get Video Element
    const videoElement = document.getElementById(videoElementId) as HTMLVideoElement;
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
    if (typeof videoDuration === "number" && !isNaN(videoDuration) && isFinite(videoDuration)) {
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
        onProgress("Recording...", "loading");
        // Get File
        const clipFile = await recordMediaStream(videoElement, cueStart, adjustedCueEnd);

        onProgress("Uploading...", "loading");

        // Request API endpoint to save the clip. Clip metadata travels as
        // headers since the request body is the streamed file.
        const headers = {
            "X-Clip-Start-Time": cueStart.toString(),
            "X-Clip-End-Time": adjustedCueEnd.toString(),
            "X-Breakdown": encodeURIComponent(JSON.stringify(breakdown)),
        };

        const response = await uploadFile<SaveClipResponse>(
            clipFile,
            "profiles/clips",
            headers,
            (progress: number) => {
                onProgress(`Uploading... ${progress.toFixed(0)}%`, "loading");
            },
            () => {
                onProgress("Saving...", "loading");
            }
        );
        if (response.clip_id) {
            onProgress("Clip saved!", "success");
        } else {
            throw new Error("Failed to save clip on the server.");
        }
    } catch (error: any) {
        console.error("Error during clip saving process:", error);
        onProgress(error.message || "An unexpected error occurred while saving the clip.", "error");
        throw error; // Re-throw to allow the caller to handle it if needed.
    }
}
