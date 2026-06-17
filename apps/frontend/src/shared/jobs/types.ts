/**
 * @packageDocumentation Types for the async job system: server-side jobs and
 * the client-side uploads that feed them, shared by the task tray and the
 * features that enqueue work.
 */

/** The long-running operations the server runs as jobs. */
export type JobType = "generate_srt" | "transcribe" | "convert" | "fix_srt";

/** A job's lifecycle status. */
export type JobStatus = "queued" | "running" | "succeeded" | "failed" | "cancelled";

/** A server-side job, mirroring the API's `JobResponse`. */
export interface Job {
    id: string;
    type: string;
    status: JobStatus;
    progress: number;
    total: number;
    completed: number;
    parent_id: string | null;
    result: Record<string, unknown> | null;
    error: string | null;
    created_at: string;
    updated_at: string;
}

/** Body for `POST /jobs`, mirroring the API's `SubmitJobRequest`. */
export interface SubmitJobRequest {
    type: JobType;
    file_id: string;
    opts?: Record<string, unknown>;
    model?: string;
    sys_msg?: string;
}

/** A stored profile file, mirroring the API's `ProfileFileResponse`. */
export interface UploadedFile {
    id: string;
    name: string;
    url: string;
    type: string | null;
    created_at: string | null;
}
