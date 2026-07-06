/**
 * @packageDocumentation Profile / dashboard feature types.
 */

/** A profile file (`/profiles/files`). */
export type ProfileFile = {
    id: string;
    name: string;
    url: string;
    type: string | null;
    folder?: string | null;
    created_at?: string | null;
};

/** A profile transcript (`/profiles/transcripts`). */
export type ProfileTranscript = {
    id: string;
    file_id: string;
    text: string;
    llm_explanation?: string | null;
    url?: string | null;
    created_at?: string | null;
};

/** Response from the Anki export endpoint. */
export interface AnkiExportResponse {
    anki_deck_url: string;
}

/**
 * Response from deleting a profile file. `deleted_job_ids` lists the jobs
 * removed alongside it (a batch parent covers its children), so the caller can
 * prune them from the task tray.
 */
export interface FileDeleteResponse {
    success: boolean;
    message: string;
    deleted_job_ids: string[];
}
