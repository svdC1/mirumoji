/**
 * @packageDocumentation Filename / URL / download helpers.
 */

import { API_BASE } from "@/shared/api/client";

/**
 * Truncates a filename to `start…end` when it's longer than the budget.
 *
 * @param {string | undefined} filename The filename.
 * @param {number} [startChars=8] Leading chars to keep.
 * @param {number} [endChars=4] Trailing chars to keep.
 * @returns {string} The (possibly) truncated name.
 */
export const truncateFilename = (filename: string | undefined, startChars = 8, endChars = 4) => {
    if (!filename) return "Unknown";
    if (filename.length > startChars + endChars + 3) {
        return `${filename.substring(0, startChars)}...${filename.substring(filename.length - endChars)}`;
    }
    return filename;
};

/**
 * Returns a file's extension (without query string), or `""`.
 *
 * @param {string | undefined} filenameOrUrl A filename or URL.
 * @returns {string} The extension.
 */
export const getFileExtension = (filenameOrUrl: string | undefined) => {
    if (!filenameOrUrl) return "";
    const parts = filenameOrUrl.split(".");
    return parts.length > 1 ? parts.pop()!.split("?")[0] : "";
};

/**
 * Truncates free text with an ellipsis.
 *
 * @param {string | undefined} text The text.
 * @param {number} [maxLength=50] The maximum length.
 * @returns {string} The truncated text.
 */
export const truncateText = (text: string | undefined, maxLength = 50) => {
    if (!text) return "";
    return text.length > maxLength ? `${text.substring(0, maxLength)}...` : text;
};

/**
 * Resolves a server-relative media path (e.g. `/media/...`) to a fetchable URL
 * behind the API base.
 *
 * @param {string} path The server path.
 * @returns {string} An absolute URL under the API base.
 */
export const staticUrl = (path: string): string =>
    path.startsWith("/") ? `${API_BASE}${path}` : `${API_BASE}/${path}`;

/**
 * Triggers a browser download of a fetched blob from a media URL.
 *
 * @param {string} url The (already resolved) URL to fetch.
 * @param {string} filename The download filename.
 * @returns {Promise<void>} Resolves once the download is triggered.
 */
export async function downloadFromUrl(url: string, filename: string): Promise<void> {
    const response = await fetch(url);
    if (!response.ok) {
        throw new Error(`HTTP ${response.status} ${response.statusText}`);
    }
    const blob = await response.blob();
    downloadBlob(blob, filename);
}

/**
 * Triggers a browser download of an in-memory blob.
 *
 * @param {Blob} blob The blob to download.
 * @param {string} filename The download filename.
 */
export function downloadBlob(blob: Blob, filename: string): void {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
}
