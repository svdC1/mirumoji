/**
 * @packageDocumentation The demo replacement for `@/shared/api/client`, aliased
 * in only for `--mode demo`. `apiFetch` answers reads from fixtures, routes the
 * job and profile-collection writes to the simulator / session store, and the
 * upload helpers fake progress. `API_BASE` is base-aware so bundled `/api/...`
 * fixtures resolve under `--base=/mirumoji/` on GitHub Pages.
 */

import { ApiError } from "@/shared/api/errors";
import { decodeFixture, lookupFixture } from "./fixtures";
import { handleJobs } from "./jobs";
import { session } from "./session";

/** `VITE_API_BASE` override, else base-aware so `/api/...` resolves under the Pages base prefix. */
export const API_BASE = import.meta.env.VITE_API_BASE ?? `${import.meta.env.BASE_URL}api`;

function parseBody(body: unknown): Record<string, unknown> | null {
    if (typeof body !== "string") return null;
    try {
        return JSON.parse(body) as Record<string, unknown>;
    } catch {
        return null;
    }
}

/** Fixture-backed `fetch` replacement mirroring the real `apiFetch` contract. */
export async function apiFetch<T = unknown>(url: string, opts: RequestInit = {}): Promise<T> {
    const method = (opts.method ?? "GET").toUpperCase();
    const path = url.split("?")[0].replace(/^\/+/, "");
    const seg = path.split("/");

    if (seg[0] === "jobs") {
        return handleJobs(method, url, opts.body) as T;
    }

    if (seg[0] === "profiles") {
        if (path === "profiles/files" && method === "GET") return session.files() as T;
        if (seg[1] === "files" && seg.length === 3 && method === "DELETE")
            return session.deleteFile(seg[2]) as T;

        if (path === "profiles/clips" && method === "GET") return session.clips() as T;
        if (seg[1] === "clips" && seg.length === 3 && method === "DELETE") {
            session.deleteClip(seg[2]);
            return undefined as T;
        }

        if (path === "profiles/transcripts" && method === "GET") return session.transcripts() as T;
        if (seg[1] === "transcripts" && seg.length === 3 && method === "DELETE") {
            session.deleteTranscript(seg[2]);
            return undefined as T;
        }

        if (path === "profiles/template") {
            if (method === "GET") {
                const t = session.template();
                if (t == null)
                    throw new ApiError(404, "No Template Set", "RecordNotFound", undefined, false);
                return t as T;
            }
            if (method === "POST") return session.setTemplate(parseBody(opts.body)) as T;
            if (method === "DELETE") {
                session.clearTemplate();
                return undefined as T;
            }
        }

        if (path === "profiles/subtitles" && method === "POST") {
            return session.saveSubtitle(String(parseBody(opts.body)?.name ?? "")) as T;
        }
    }

    // The template editor's live preview renders an arbitrary edited prompt,
    // which has no fixture. Answer any un-recorded preview with a friendly line
    // rather than a 404 so editing the template does not error.
    if (path === "llm/breakdown/preview" && method === "POST") {
        const preview = lookupFixture(method, url, opts.body);
        return (
            preview
                ? decodeFixture(preview)
                : { prompt: "Live Preview Is Limited In The Demo Sample" }
        ) as T;
    }

    const fx = lookupFixture(method, url, opts.body);
    if (!fx) {
        // An off-fixture read (an out-of-set dictionary target, ...) is a 404
        // that read views degrade to "Nothing Found", with no network call.
        throw new ApiError(404, "Not Available In The Demo", "RecordNotFound", undefined, false);
    }
    if (fx.status >= 400) {
        throw new ApiError(fx.status, "Request Failed", undefined, undefined, false);
    }
    return decodeFixture(fx) as T;
}

/** Fakes a profile-file upload; the file bytes are ignored (the sample is canned). */
export async function uploadFile<T = unknown>(
    file: File,
    url: string,
    _headers: Record<string, string>,
    onProgress: (percent: number) => void,
    onUploadComplete: () => void
): Promise<T> {
    onProgress(100);
    onUploadComplete();
    const type = new URLSearchParams(url.split("?")[1] ?? "").get("type") ?? undefined;
    return session.addFile(file.name, type) as T;
}

/** Fakes a multipart upload; for a saved clip the recorded blob is played back locally. */
export async function uploadFormData<T = unknown>(
    _url: string,
    formData: FormData,
    onProgress: (percent: number) => void,
    onUploadComplete: () => void
): Promise<T> {
    onProgress(100);
    onUploadComplete();
    const blob = formData.get("clip_file");
    const start = Number(formData.get("start_time") ?? 0);
    const end = Number(formData.get("end_time") ?? 0);
    let breakdown: unknown = null;
    try {
        breakdown = JSON.parse(String(formData.get("breakdown") ?? "null"));
    } catch {
        breakdown = null;
    }
    return session.addClip(blob as Blob, start, end, breakdown) as T;
}
