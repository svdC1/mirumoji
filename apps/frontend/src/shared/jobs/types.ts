/**
 * @packageDocumentation Types for the async job system: server-side jobs and
 * the client-side uploads that feed them, shared by the task tray and the
 * features that enqueue work.
 */

/** The single-file long-running operations the server runs as jobs. */
export type JobType = "generate_srt" | "transcribe" | "convert" | "fix_srt";

/** The batch operations, each running one single-op across many files. */
export type BatchJobType =
    | "batch_generate_srt"
    | "batch_transcribe"
    | "batch_convert"
    | "batch_fix_srt";

/** A job's lifecycle status. */
export type JobStatus = "queued" | "running" | "succeeded" | "failed" | "cancelled";

/**
 * Curated transcription options, mirroring the server's `TranscribeOptions`.
 * Every field is optional: an unset field is omitted from the request, so the
 * server falls back to its own tuned defaults.
 */
export interface TranscribeOpts {
    language?: string;
    beam_size?: number;
    best_of?: number;
    patience?: number;
    length_penalty?: number;
    temperature?: number;
    compression_ratio_threshold?: number;
    log_prob_threshold?: number;
    no_speech_threshold?: number;
    condition_on_previous_text?: boolean;
    initial_prompt?: string;
    vad_filter?: boolean;
}

/** Conversion options, mirroring the server's `ConvertVideoRequest`. */
export interface ConvertOpts {
    resolution?: string;
    target_bitrate?: string;
}

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
    error_code: string | null;
    error_details: Record<string, unknown> | null;
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

/**
 * Body for `POST /jobs/batch`, mirroring the API's `SubmitBatchRequest`. One
 * child job is created per `file_id`, all sharing the same options.
 */
export interface BatchSubmitRequest {
    type: BatchJobType;
    file_ids: string[];
    opts?: Record<string, unknown>;
    model?: string;
    sys_msg?: string;
}

/** Result of a `batch_*` parent job (the server's `BatchResult`). */
export interface BatchResult {
    total: number;
    succeeded: number;
    failed: number;
    cancelled: number;
    children: string[];
}

/** A stored profile file, mirroring the API's `ProfileFileResponse`. */
export interface UploadedFile {
    id: string;
    name: string;
    url: string;
    type: string | null;
    folder: string | null;
    created_at: string | null;
}

/** Result of a `generate_srt` or `fix_srt` job (the server's `SrtResult`). */
export interface SrtResult {
    srt_file_id: string;
    srt_url: string;
    srt_content: string;
}

/** Result of a `transcribe` job (the server's `TranscribeResult`). */
export interface TranscribeResult {
    transcript_id: string;
    transcript: string;
}

/** Result of a `convert` job (the server's `ConvertResult`). */
export interface ConvertResult {
    file_id: string;
    video_url: string;
}
