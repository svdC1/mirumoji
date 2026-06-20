/**
 * @packageDocumentation Display helpers for jobs: human labels per operation
 * type, the "apply result" action labels, the active-status test, and the
 * status line (including batch progress + outcome summaries). Shared by the task
 * tray and the dashboard Tasks tab.
 */

import type { BatchResult, Job, JobStatus } from "./types";

/** Human label per job type (single + batch). */
export const TYPE_LABELS: Record<string, string> = {
    generate_srt: "Generate Subtitles",
    transcribe: "Transcribe",
    convert: "Convert To MP4",
    fix_srt: "Fix Subtitles",
    batch_generate_srt: "Batch · Generate Subtitles",
    batch_transcribe: "Batch · Transcribe",
    batch_convert: "Batch · Convert To MP4",
    batch_fix_srt: "Batch · Fix Subtitles",
};

/** The "apply this result" action label per single-op type. */
export const RESULT_LABELS: Record<string, string> = {
    generate_srt: "Load Subtitles",
    fix_srt: "Load Subtitles",
    convert: "Open Video",
    transcribe: "View Transcript",
};

/**
 * The display label for a job type.
 *
 * @param {string} type The job type.
 * @returns {string} The human label (falls back to the raw type).
 */
export function typeLabel(type: string): string {
    return TYPE_LABELS[type] ?? type;
}

/**
 * Whether a status is still in flight.
 *
 * @param {JobStatus} status The status.
 * @returns {boolean} `true` for queued / running.
 */
export function isActive(status: JobStatus): boolean {
    return status === "queued" || status === "running";
}

/** A finished batch's per-file outcome summary (e.g. "5 Done · 1 Failed"). */
function batchSummary(job: Job): string {
    const result = job.result as unknown as BatchResult | null;
    if (!result) return "Done";
    const parts = [`${result.succeeded} Done`];
    if (result.failed) parts.push(`${result.failed} Failed`);
    if (result.cancelled) parts.push(`${result.cancelled} Cancelled`);
    return parts.join(" · ");
}

/**
 * The short status line for a job (batch-aware).
 *
 * @param {Job} job The job.
 * @returns {string} The status line.
 */
export function statusText(job: Job): string {
    const isBatch = job.total > 1;
    switch (job.status) {
        case "queued":
            return "Queued";
        case "running":
            return isBatch ? `Running · ${job.completed} / ${job.total}` : "Running";
        case "succeeded":
            return isBatch ? batchSummary(job) : "Done";
        case "failed":
            // Short + structured; the full message goes to a toast (mapped).
            return job.error_code ? `Failed · ${job.error_code}` : "Failed";
        case "cancelled":
            return "Cancelled";
        default:
            return job.status;
    }
}
