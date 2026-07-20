/**
 * @packageDocumentation A `fetch` wrapper + a progress-tracked
 * file upload, both injecting the active profile header and parsing the
 * server's structured error envelope.
 */

import { ApiError } from "./errors";

/**
 * Single source of truth for the API base. Overridable at build time via
 * `VITE_API_BASE` (defaults to `/api`, which the dev server proxies), for
 * deployments that serve the API from a different path or host.
 */
export const API_BASE = import.meta.env.VITE_API_BASE ?? "/api";

/**
 * Parses a server error body into a message + optional machine code/details,
 * understanding the nested `{ error: { code, message, details } }` envelope.
 * A body that isn't that envelope (a static host's 404 HTML, a dev-proxy error
 * page, ...) yields a generic message flagged `displayMessage: false` so callers
 * never surface raw markup to the user.
 */
function parseApiError(
    body: string,
    status: number
): { message: string; code?: string; details?: unknown; displayMessage: boolean } {
    try {
        const parsed = JSON.parse(body);
        if (
            parsed &&
            typeof parsed === "object" &&
            parsed.error &&
            typeof parsed.error.message === "string"
        ) {
            return {
                message: parsed.error.message,
                code: parsed.error.code,
                details: parsed.error.details,
                displayMessage: true,
            };
        }
    } catch {
        // body wasn't the JSON envelope (HTML page, proxy error, ...)
    }
    return { message: `Request Failed (${status})`, displayMessage: false };
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

    let res: Response;
    try {
        res = await fetch(fullUrl, { ...opts, headers });
    } catch {
        // Network failure / server down / DNS / CORS — the backend is unreachable.
        throw new ApiError(0, "Could not reach the server", "BackendUnreachable", undefined, false);
    }

    if (!res.ok) {
        const body = await res.text();
        const { message, code, details, displayMessage } = parseApiError(body, res.status);
        throw new ApiError(res.status, message, code, details, displayMessage);
    }

    // A 204 carries no body (a DELETE), but the server still tags it
    // application/json, so parsing it as JSON would throw on the empty body.
    if (res.status === 204) {
        return undefined as T;
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
 * The `ApiError` code reported when an upload is cancelled by the caller.
 *
 * Distinguishes a deliberate cancel from a genuine failure, so the tray drops
 * the row instead of showing it as an error.
 */
export const UPLOAD_ABORTED_CODE = "UploadAborted";

/**
 * Whether an error is an upload the caller cancelled, rather than a failure.
 *
 * @param {unknown} error The caught error.
 * @returns {boolean} `true` when the upload was aborted deliberately.
 */
export function isUploadAborted(error: unknown): boolean {
    return error instanceof ApiError && error.code === UPLOAD_ABORTED_CODE;
}

/**
 * Wires the shared progress + completion handling for an upload `XMLHttpRequest`
 * (progress events, the 2xx/JSON-parse success path, the structured-error path,
 * the unreachable-server path, and the caller-cancelled path), so the upload
 * helpers only differ in how they build and send the request.
 */
function settleUpload<T>(
    xhr: XMLHttpRequest,
    resolve: (value: T) => void,
    reject: (reason: ApiError) => void,
    onProgress: (percent: number) => void,
    onUploadComplete: () => void,
    signal?: AbortSignal
): void {
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
            const { message, code, details, displayMessage } = parseApiError(
                xhr.responseText,
                xhr.status
            );
            reject(new ApiError(xhr.status, message, code, details, displayMessage));
        }
    };

    xhr.onerror = () =>
        reject(
            new ApiError(0, "Could not reach the server", "BackendUnreachable", undefined, false)
        );

    // Without this, calling `abort()` fires `onabort` (never `onerror`) and the
    // promise would stay pending forever.
    xhr.onabort = () =>
        reject(new ApiError(0, "Upload Cancelled", UPLOAD_ABORTED_CODE, undefined, false));

    if (signal) {
        if (signal.aborted) {
            xhr.abort();
            return;
        }
        const onAbort = () => xhr.abort();
        signal.addEventListener("abort", onAbort, { once: true });
        // Detach once the request settles, so a long-lived controller does not
        // retain the xhr after it is done.
        xhr.onloadend = () => signal.removeEventListener("abort", onAbort);
    }
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
 * @param {AbortSignal} [signal] Cancels the upload when aborted, rejecting with
 *   an {@link ApiError} carrying {@link UPLOAD_ABORTED_CODE}.
 * @returns {Promise<T>} The parsed JSON response.
 */
export async function uploadFile<T = unknown>(
    file: File,
    url: string,
    headers: Record<string, string>,
    onProgress: (percent: number) => void,
    onUploadComplete: () => void,
    signal?: AbortSignal
): Promise<T> {
    return new Promise((resolve, reject) => {
        const fullUrl = url.startsWith("http") ? url : `${API_BASE}/${url}`;
        const profileId = localStorage.getItem("currentProfileId");
        if (!profileId) {
            return reject(new ApiError(400, "No Profile ID Found. Select A Profile"));
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

        settleUpload(xhr, resolve, reject, onProgress, onUploadComplete, signal);
        xhr.send(file);
    });
}

/**
 * Uploads `multipart/form-data` via a progress-tracked `XMLHttpRequest`,
 * mirroring {@link uploadFile} (profile header, {@link ApiError}, JSON
 * response). The file rides in the form body, so large structured metadata is
 * a form field rather than a size-limited header. The browser sets the
 * multipart `Content-Type` (with boundary), so it is deliberately not set here.
 *
 * @template T The expected JSON response type.
 * @param {string} url The API endpoint.
 * @param {FormData} formData The multipart payload (file part + fields).
 * @param {(percent: number) => void} onProgress Upload progress callback.
 * @param {() => void} onUploadComplete Called when the upload hits 100%.
 * @param {AbortSignal} [signal] Cancels the upload when aborted, rejecting with
 *   an {@link ApiError} carrying {@link UPLOAD_ABORTED_CODE}.
 * @returns {Promise<T>} The parsed JSON response.
 */
export async function uploadFormData<T = unknown>(
    url: string,
    formData: FormData,
    onProgress: (percent: number) => void,
    onUploadComplete: () => void,
    signal?: AbortSignal
): Promise<T> {
    return new Promise((resolve, reject) => {
        const fullUrl = url.startsWith("http") ? url : `${API_BASE}/${url}`;
        const profileId = localStorage.getItem("currentProfileId");
        if (!profileId) {
            return reject(new ApiError(400, "No Profile ID Found. Select A Profile"));
        }

        const xhr = new XMLHttpRequest();
        xhr.open("POST", fullUrl, true);
        xhr.setRequestHeader("X-Profile-ID", profileId);

        settleUpload(xhr, resolve, reject, onProgress, onUploadComplete, signal);
        xhr.send(formData);
    });
}
