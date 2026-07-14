/**
 * @packageDocumentation The demo's in-memory write store. The hybrid policy lets
 * harmless writes (save a clip, delete, edit the template) feel real for the
 * session and reset on reload. Mutable profile collections start from their
 * recorded GET fixtures and apply an overlay of session additions/deletions.
 */

import { lookupFixture } from "./fixtures";

interface SessionState {
    files: unknown[];
    clips: unknown[];
    transcripts: unknown[];
    template: unknown | null;
    /** URLs minted for session-recorded clips, revoked is left to page reload. */
    objectUrls: string[];
}

/** Reads a recorded list fixture as the starting point for an overlay. */
function initialList(url: string): unknown[] {
    const fx = lookupFixture("GET", url);
    return fx && Array.isArray(fx.body) ? [...(fx.body as unknown[])] : [];
}

function initialTemplate(): unknown | null {
    const fx = lookupFixture("GET", "profiles/template");
    return fx && fx.status < 400 ? fx.body : null;
}

const state: SessionState = {
    files: initialList("profiles/files"),
    clips: initialList("profiles/clips"),
    transcripts: initialList("profiles/transcripts"),
    template: initialTemplate(),
    objectUrls: [],
};

let counter = 0;
const nextId = (prefix: string): string => `demo-${prefix}-${++counter}`;

/** The `id` field of a record, tolerant of the id key each collection uses. */
function idOf(record: unknown, keys: string[]): string | undefined {
    const obj = record as Record<string, unknown> | null;
    for (const k of keys) {
        if (obj && typeof obj[k] === "string") return obj[k] as string;
    }
    return undefined;
}

export const session = {
    files: (): unknown[] => state.files,
    clips: (): unknown[] => state.clips,
    transcripts: (): unknown[] => state.transcripts,
    template: (): unknown | null => state.template,

    deleteFile(id: string): { success: boolean; message: string; deleted_job_ids: string[] } {
        state.files = state.files.filter((f) => idOf(f, ["id", "file_id"]) !== id);
        return { success: true, message: "Deleted", deleted_job_ids: [] };
    },

    deleteClip(id: string): void {
        state.clips = state.clips.filter((c) => idOf(c, ["id", "clip_id"]) !== id);
    },

    deleteTranscript(id: string): void {
        state.transcripts = state.transcripts.filter((t) => idOf(t, ["id"]) !== id);
    },

    setTemplate(body: unknown): unknown {
        state.template = body;
        return body;
    },

    clearTemplate(): void {
        state.template = null;
    },

    /** Registers an uploaded profile file and returns a synthesized record. */
    addFile(name: string, type?: string): Record<string, unknown> {
        const file = {
            id: nextId("file"),
            name,
            url: "",
            type: type ?? "unknown",
            folder: null,
            source_file_id: null,
            origin: "uploaded",
            created_at: new Date().toISOString(),
        };
        state.files = [file, ...state.files];
        return file;
    },

    /**
     * Registers a session-saved clip. The recorder produced a real blob, so we
     * mint an object URL for it and play it back locally this session.
     */
    addClip(
        blob: Blob,
        startTime: number,
        endTime: number,
        breakdown: unknown
    ): { clip_id: string; file_id: string; clip_url: string } {
        const clipId = nextId("clip");
        const fileId = nextId("file");
        const clipUrl = URL.createObjectURL(blob);
        state.objectUrls.push(clipUrl);
        const clip = {
            id: clipId,
            file_id: fileId,
            clip_url: clipUrl,
            start_time: startTime,
            end_time: endTime,
            breakdown,
        };
        state.clips = [clip, ...state.clips];
        return { clip_id: clipId, file_id: fileId, clip_url: clipUrl };
    },

    /** Records a saved subtitle file and returns a synthesized record. */
    saveSubtitle(name: string): Record<string, unknown> {
        const file = {
            id: nextId("file"),
            name: name || "subtitles.srt",
            url: "",
            type: "srt",
            folder: null,
            source_file_id: null,
            origin: "saved",
            created_at: new Date().toISOString(),
        };
        state.files = [file, ...state.files];
        return file;
    },
};
