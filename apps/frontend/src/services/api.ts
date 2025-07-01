/**
 * @fileoverview This file contains the apiFetch function, which is a wrapper around the native fetch function.
 */

import { ApiError } from "../types/types";

const BASE = "api";

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
    const fullUrl = url.startsWith("http") ? url : `${BASE}${url}`;

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
