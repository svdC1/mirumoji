/**
 * @packageDocumentation Player video API helpers. The long-running operations
 * (SRT generation, MP4 convert, LLM fix) now run as jobs via the task tray;
 * this only keeps the direct SRT-save helper.
 */

import { apiFetch } from "@/shared/api/client";
import type { ProfileFile } from "@/features/profile/types";

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
