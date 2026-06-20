/**
 * @packageDocumentation Records a video segment and uploads it as a saved clip.
 */

import { uploadFormData } from "@/shared/api/client";
import { recordMediaStream } from "./recorder";
import type { ClipBreakdown, SaveClipResponse } from "./types";

/**
 * Records a segment from a video element, bundles it with its breakdown, and
 * uploads it as a saved clip.
 *
 * @param {string} videoElementId The id of the source HTMLVideoElement.
 * @param {number} cueStart Clip start time (seconds).
 * @param {number} cueEnd Clip end time (seconds).
 * @param {ClipBreakdown} breakdown The breakdown payload to store.
 * @param {(message: string, type: "success" | "error" | "loading") => void} onProgress
 *     Progress callback.
 * @returns {Promise<void>} Resolves when saved, rejects on error.
 */
export async function createAndSaveClip(
    videoElementId: string,
    cueStart: number,
    cueEnd: number,
    breakdown: ClipBreakdown,
    onProgress: (message: string, type: "success" | "error" | "loading") => void
): Promise<void> {
    const videoElement = document.getElementById(videoElementId) as HTMLVideoElement | null;
    if (!videoElement) {
        onProgress("Video player not found.", "error");
        throw new Error("Video player not found.");
    }

    // Pad the end by 1s to catch phrase cuts, clamped to the video duration.
    let adjustedCueEnd = cueEnd + 1.0;
    if (cueStart >= adjustedCueEnd) {
        onProgress("Clip start time is after end time.", "error");
        throw new Error("Clip start time is after end time");
    }

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
        // No known duration (e.g. streams): drop the padding.
        adjustedCueEnd = cueEnd;
    }

    try {
        onProgress("Recording...", "loading");
        const clipFile = await recordMediaStream(videoElement, cueStart, adjustedCueEnd);

        onProgress("Uploading...", "loading");
        // Clip + metadata travel together as multipart form fields, so the
        // breakdown is a body field rather than a size-limited header.
        const formData = new FormData();
        formData.append("clip_file", clipFile);
        formData.append("start_time", cueStart.toString());
        formData.append("end_time", adjustedCueEnd.toString());
        formData.append("breakdown", JSON.stringify(breakdown));

        const response = await uploadFormData<SaveClipResponse>(
            "profiles/clips",
            formData,
            (progress: number) => onProgress(`Uploading... ${progress.toFixed(0)}%`, "loading"),
            () => onProgress("Saving...", "loading")
        );

        if (response.clip_id) {
            onProgress("Clip saved!", "success");
        } else {
            throw new Error("Failed to save clip on the server.");
        }
    } catch (error) {
        console.error("Error during clip saving process:", error);
        const message =
            error instanceof Error
                ? error.message
                : "An unexpected error occurred while saving the clip.";
        onProgress(message, "error");
        throw error;
    }
}
