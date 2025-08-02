/**
 * @packageDocumentation This file contains the apiFetch function, which is a wrapper around the native fetch function.
 */

import { ApiError } from "../types/types";

const BASE = "/api";

/**
 * A fetch replacement that:
 *   - Auto-prefixes BASE for relative URLs
 *   - Adds X-Profile-ID header if a profile is set in localStorage
 *   - Throws ApiError on non-2xx
 *   - Parses JSON/text/blob based on content-type
 *
 * @param {string} url The URL to fetch.
 * @param {RequestInit} [opts={}] The options for the fetch request.
 * @returns {Promise<T>} A promise that resolves to the response data.
 * @template T
 */
export async function apiFetch<T = unknown>(
    url: string,
    opts: RequestInit = {}
): Promise<T> {
    // build the full URL
    const fullUrl = url.startsWith("http") ? url : `${BASE}/${url}`;

    // merge / build headers
    const headers = new Headers(opts.headers as HeadersInit);
    if (!(opts.body instanceof FormData) && !headers.has("Content-Type")) {
        headers.set("Content-Type", "application/json");
    }

    // Add Profile ID header if available
    const profileId = localStorage.getItem("currentProfileId");
    if (profileId) {
        headers.set("X-Profile-ID", profileId);
    }

    const res = await fetch(fullUrl, { ...opts, headers });

    if (!res.ok) {
        const msg = (await res.text()) || res.statusText;
        throw new ApiError(res.status, msg);
    }

    const ct = res.headers.get("content-type") ?? "";
    if (ct.includes("application/json")) {
        return res.json() as Promise<T>;
    }
    if (ct.startsWith("text/")) {
        return res.text() as unknown as T;
    }
    // fallback to blob
    return res.blob() as unknown as T;
}

/**
 * Uploads a file to the server using a streaming request with progress tracking.
 * It mirrors the behavior of `apiFetch` by automatically adding the profile ID,
 * handling errors with `ApiError`, and providing a consistent API.
 *
 * @template T The expected type of the JSON response.
 * @param {File} file The file to upload.
 * @param {string} url The API endpoint to upload the file to.
 * @param {Object.<string, string>} headers A dictionary of additional headers to send with the request.
 * @param {(percent: number) => void} onProgress A callback function that receives the upload progress as a percentage.
 * @param {() => void} onUploadComplete A callback function that is triggered when the upload portion is 100% complete.
 * @returns {Promise<T>} A promise that resolves with the JSON response from the server.
 */
export async function uploadFile<T = unknown>(
    file: File,
    url: string,
    headers: { [key: string]: string },
    onProgress: (percent: number) => void,
    onUploadComplete: () => void
): Promise<T> {
    return new Promise((resolve, reject) => {
        const fullUrl = url.startsWith("http") ? url : `${BASE}/${url}`;
        const profileId = localStorage.getItem("currentProfileId");
        if (!profileId) {
            return reject(
                new ApiError(
                    400,
                    "No profile ID found. Please select a profile."
                )
            );
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
                    const response = JSON.parse(xhr.responseText);
                    resolve(response as T);
                } catch (e) {
                    reject(
                        new ApiError(500, "Failed to parse server response.")
                    );
                }
            } else {
                const msg =
                    xhr.responseText ||
                    `Request failed with status ${xhr.status}`;
                reject(new ApiError(xhr.status, msg));
            }
        };

        xhr.onerror = () => {
            reject(new ApiError(500, "Network Error"));
        };

        xhr.send(file);
    });
}
