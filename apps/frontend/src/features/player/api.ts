/**
 * @packageDocumentation Player video API helpers (SRT generation + MP4 convert).
 */

import { apiFetch, uploadFile } from "@/shared/api/client";
import type { ProfileFile } from "@/features/profile/types";
import type { ConvertVideoResponse, GenerateSrtResponse } from "./types";

/**
 * Persists SRT content to the active profile (`POST /profiles/subtitles`).
 * Pass `file_id` to overwrite an existing profile SRT in place (e.g. after
 * fixing it); omit it to store a new SRT file.
 *
 * @param {object} req The save request.
 * @param {string} req.content The SRT content.
 * @param {string} [req.file_id] An existing SRT file id to overwrite.
 * @param {string} [req.name] A name for a newly created file.
 * @returns {Promise<ProfileFile>} The stored SRT file record.
 */
export function saveSubtitles(req: {
    content: string;
    file_id?: string;
    name?: string;
}): Promise<ProfileFile> {
    return apiFetch<ProfileFile>("profiles/subtitles", {
        method: "POST",
        body: JSON.stringify(req),
    });
}

/**
 * Generates raw SRT subtitles from a video upload (`/video/generate_srt`).
 *
 * @param {File} file The video file.
 * @param {(percent: number) => void} onProgress Upload progress callback.
 * @param {() => void} onUploadComplete Called when the upload reaches 100%.
 * @returns {Promise<GenerateSrtResponse>} The generated SRT (content + url + id).
 */
export function generateSrt(
    file: File,
    onProgress: (percent: number) => void,
    onUploadComplete: () => void
): Promise<GenerateSrtResponse> {
    return uploadFile<GenerateSrtResponse>(
        file,
        "video/generate_srt",
        {},
        onProgress,
        onUploadComplete
    );
}

/**
 * Converts a video upload to MP4 (`/video/convert_to_mp4`).
 *
 * @param {File} file The video file.
 * @param {(percent: number) => void} onProgress Upload progress callback.
 * @param {() => void} onUploadComplete Called when the upload reaches 100%.
 * @returns {Promise<ConvertVideoResponse>} The converted video URL.
 */
export function convertToMp4(
    file: File,
    onProgress: (percent: number) => void,
    onUploadComplete: () => void
): Promise<ConvertVideoResponse> {
    return uploadFile<ConvertVideoResponse>(
        file,
        "video/convert_to_mp4",
        {},
        onProgress,
        onUploadComplete
    );
}
