/**
 * @packageDocumentation Profile data API — files, transcripts, clips, and the
 * Anki export. (LLM template CRUD lives in shared/llm/api.)
 */

import { apiFetch } from "@/shared/api/client";
import type { Clip } from "@/shared/clips/types";
import type {
    AnkiExportResponse,
    FileDeleteResponse,
    ProfileFile,
    ProfileTranscript,
} from "./types";

/** Lists the active profile's files (`GET /profiles/files`). */
export function listFiles(): Promise<ProfileFile[]> {
    return apiFetch<ProfileFile[]>("profiles/files", { method: "GET" });
}

/**
 * Deletes a profile file by id (`DELETE /profiles/files/{id}`), returning the
 * ids of the jobs it cascaded away so the caller can prune the task tray.
 */
export function deleteFile(fileId: string): Promise<FileDeleteResponse> {
    return apiFetch<FileDeleteResponse>(`profiles/files/${fileId}`, { method: "DELETE" });
}

/** Lists the active profile's transcripts (`GET /profiles/transcripts`). */
export function listTranscripts(): Promise<ProfileTranscript[]> {
    return apiFetch<ProfileTranscript[]>("profiles/transcripts", { method: "GET" });
}

/** Deletes a transcript by id (`DELETE /profiles/transcripts/{id}`). */
export async function deleteTranscript(transcriptId: string): Promise<void> {
    await apiFetch(`profiles/transcripts/${transcriptId}`, { method: "DELETE" });
}

/** Lists the active profile's saved clips (`GET /profiles/clips`). */
export function listClips(): Promise<Clip[]> {
    return apiFetch<Clip[]>("profiles/clips", { method: "GET" });
}

/** Deletes a clip by id (`DELETE /profiles/clips/{id}`). */
export async function deleteClip(clipId: string): Promise<void> {
    await apiFetch(`profiles/clips/${clipId}`, { method: "DELETE" });
}

/** Exports all clips as an Anki deck (`GET /profiles/anki_export`). */
export function exportAnki(): Promise<AnkiExportResponse> {
    return apiFetch<AnkiExportResponse>("profiles/anki_export", { method: "GET" });
}
