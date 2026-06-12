/**
 * @packageDocumentation A `fetch` wrapper + a progress-tracked
 * file upload, both injecting the active profile header and parsing the
 * server's structured error envelope.
 */

import { ApiError } from "./errors";

/** Single source of truth for the API base (dev server proxies `/api`). */
export const API_BASE = "/api";

/**
 * Parses a server error body into a message + optional machine code/details,
 * understanding the nested `{ error: { code, message, details } }` envelope.
 */
function parseApiError(
    body: string,
    fallback: string
): { message: string; code?: string; details?: unknown } {
    try {
        const parsed = JSON.parse(body);
        if (parsed && typeof parsed === "object" && parsed.error) {
            return {
                message: parsed.error.message ?? fallback,
                code: parsed.error.code,
                details: parsed.error.details,
            };
        }
    } catch {
        // body wasn't JSON; fall through to the raw text
    }
    return { message: body || fallback };
}

/**
 * A `fetch` replacement that prefixes the API base for relative URLs, injects
 * the `X-Profile-ID` header, throws {@link ApiError} on non-2xx, and parses the
 * response by content-type.
 *
 * @param {string} url Relative API path (or absolute URL).
 * @param {RequestInit} [opts={}] Fetch options.
 * @returns {Promise<T>} The parsed response.
 * @template T
 */
export async function apiFetch<T = unknown>(url: string, opts: RequestInit = {}): Promise<T> {
    const fullUrl = url.startsWith("http") ? url : `${API_BASE}/${url}`;

    const headers = new Headers(opts.headers as HeadersInit);
    if (!(opts.body instanceof FormData) && !headers.has("Content-Type")) {
        headers.set("Content-Type", "application/json");
    }

    const profileId = localStorage.getItem("currentProfileId");
    if (profileId) {
        headers.set("X-Profile-ID", profileId);
    }

    const res = await fetch(fullUrl, { ...opts, headers });

    if (!res.ok) {
        const body = await res.text();
        const { message, code, details } = parseApiError(body, res.statusText);
        throw new ApiError(res.status, message, code, details);
    }

    const ct = res.headers.get("content-type") ?? "";
    if (ct.includes("application/json")) {
        return res.json() as Promise<T>;
    }
    if (ct.startsWith("text/")) {
        return res.text() as unknown as T;
    }
    return res.blob() as unknown as T;
}

/**
 * Uploads a file via a streaming `XMLHttpRequest` with progress, mirroring
 * `apiFetch` (profile header, {@link ApiError}, JSON response).
 *
 * @template T The expected JSON response type.
 * @param {File} file The file to upload.
 * @param {string} url The API endpoint.
 * @param {Record<string, string>} headers Additional request headers.
 * @param {(percent: number) => void} onProgress Upload progress callback.
 * @param {() => void} onUploadComplete Called when the upload hits 100%.
 * @returns {Promise<T>} The parsed JSON response.
 */
export async function uploadFile<T = unknown>(
    file: File,
    url: string,
    headers: Record<string, string>,
    onProgress: (percent: number) => void,
    onUploadComplete: () => void
): Promise<T> {
    return new Promise((resolve, reject) => {
        const fullUrl = url.startsWith("http") ? url : `${API_BASE}/${url}`;
        const profileId = localStorage.getItem("currentProfileId");
        if (!profileId) {
            return reject(new ApiError(400, "No profile ID found. Please select a profile."));
        }

        const uploadId = `${file.name}-${Date.now()}`;
        const xhr = new XMLHttpRequest();

        xhr.open("POST", fullUrl, true);
        xhr.setRequestHeader("X-Upload-ID", uploadId);
        xhr.setRequestHeader("X-File-Name", file.name);
        xhr.setRequestHeader("X-Profile-ID", profileId);
        xhr.setRequestHeader("Content-Type", "application/octet-stream");

        for (const key in headers) {
            xhr.setRequestHeader(key, headers[key]);
        }

        xhr.upload.onprogress = (event) => {
            if (event.lengthComputable) {
                const percentComplete = (event.loaded / event.total) * 100;
                onProgress(percentComplete);
                if (percentComplete === 100) {
                    onUploadComplete();
                }
            }
        };

        xhr.onload = () => {
            if (xhr.status >= 200 && xhr.status < 300) {
                try {
                    resolve(JSON.parse(xhr.responseText) as T);
                } catch {
                    reject(new ApiError(500, "Failed to parse server response."));
                }
            } else {
                const { message, code, details } = parseApiError(
                    xhr.responseText,
                    `Request failed with status ${xhr.status}`
                );
                reject(new ApiError(xhr.status, message, code, details));
            }
        };

        xhr.onerror = () => reject(new ApiError(500, "Network Error"));
        xhr.send(file);
    });
}
