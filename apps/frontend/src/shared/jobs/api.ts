/**
 * @packageDocumentation Thin client for the job system endpoints (`/jobs`) and
 * the upload-once endpoint (`POST /profiles/files`) that feeds them.
 */

import { apiFetch, uploadFile } from "@/shared/api/client";
import type { Job, SubmitJobRequest, UploadedFile } from "./types";

/**
 * Lists the active profile's top-level jobs.
 *
 * @param {boolean} [activeOnly=false] Restrict to queued / running jobs.
 * @returns {Promise<Job[]>} The jobs, newest first.
 */
export function listJobs(activeOnly = false): Promise<Job[]> {
    return apiFetch<Job[]>(`jobs${activeOnly ? "?active=true" : ""}`);
}

/**
 * Fetches a single job.
 *
 * @param {string} id The job id.
 * @returns {Promise<Job>} The job.
 */
export function getJob(id: string): Promise<Job> {
    return apiFetch<Job>(`jobs/${id}`);
}

/**
 * Submits a job against an already-uploaded profile file.
 *
 * @param {SubmitJobRequest} req The submission.
 * @returns {Promise<Job>} The created job.
 */
export function submitJob(req: SubmitJobRequest): Promise<Job> {
    return apiFetch<Job>("jobs", { method: "POST", body: JSON.stringify(req) });
}

/**
 * Cancels a queued or running job.
 *
 * @param {string} id The job id.
 * @returns {Promise<Job>} The updated job.
 */
export function cancelJob(id: string): Promise<Job> {
    return apiFetch<Job>(`jobs/${id}/cancel`, { method: "POST" });
}

/**
 * Uploads a file as a profile file (no processing), for later job submission.
 *
 * @param {File} file The file to upload.
 * @param {string | undefined} type Optional file-type tag.
 * @param {(percent: number) => void} onProgress Upload progress callback.
 * @param {() => void} onComplete Called when the upload hits 100%.
 * @returns {Promise<UploadedFile>} The stored file.
 */
export function uploadProfileFile(
    file: File,
    type: string | undefined,
    onProgress: (percent: number) => void,
    onComplete: () => void
): Promise<UploadedFile> {
    const url = type ? `profiles/files?type=${encodeURIComponent(type)}` : "profiles/files";
    return uploadFile<UploadedFile>(file, url, {}, onProgress, onComplete);
}
