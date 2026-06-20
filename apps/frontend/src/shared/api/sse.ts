/**
 * @packageDocumentation A reusable Server-Sent Events client over `fetch` (an
 * `EventSource` can't POST a JSON body), mirroring `apiFetch` (profile header,
 * {@link ApiError}). Each `data:` frame is JSON; a named `error` event aborts
 * with an {@link ApiError}, and the stream ends on the `done` event.
 */

import { API_BASE } from "./client";
import { ApiError } from "./errors";

/** Per-frame callbacks for a streamed response. */
export interface SSEHandlers {
    /** A decoded text chunk of the answer. */
    onToken: (token: string) => void;
    /** A named non-data event (e.g. breakdown's `focus`), with its JSON data. */
    onEvent?: (event: string, dataJson: string) => void;
}

/**
 * POSTs `body` and streams the Server-Sent Events response, invoking the
 * handlers per frame until the terminal `done` event.
 *
 * @param {string} url The relative API path.
 * @param {unknown} body The JSON request body.
 * @param {SSEHandlers} handlers Per-frame callbacks.
 * @param {AbortSignal} [signal] Aborts the stream.
 * @returns {Promise<void>} Resolves at the `done` event.
 * @throws {ApiError} On a non-2xx response or a streamed `error` event.
 */
export async function streamSSE(
    url: string,
    body: unknown,
    handlers: SSEHandlers,
    signal?: AbortSignal
): Promise<void> {
    const profileId = localStorage.getItem("currentProfileId");
    let res: Response;
    try {
        res = await fetch(`${API_BASE}/${url}`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                ...(profileId ? { "X-Profile-ID": profileId } : {}),
            },
            body: JSON.stringify(body),
            signal,
        });
    } catch {
        throw new ApiError(0, "Could not reach the server", "BackendUnreachable", undefined, false);
    }

    if (!res.ok || !res.body) {
        const text = await res.text().catch(() => "");
        let message = `Request Failed (${res.status})`;
        let code: string | undefined;
        try {
            const parsed = JSON.parse(text);
            if (parsed?.error?.message) {
                message = parsed.error.message;
                code = parsed.error.code;
            }
        } catch {
            /* not the JSON error envelope */
        }
        throw new ApiError(res.status, message, code);
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    for (;;) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        let sep: number;
        while ((sep = buffer.indexOf("\n\n")) !== -1) {
            const frame = buffer.slice(0, sep);
            buffer = buffer.slice(sep + 2);

            let event = "message";
            const dataLines: string[] = [];
            for (const line of frame.split("\n")) {
                if (line.startsWith("event:")) {
                    event = line.slice(6).trim();
                } else if (line.startsWith("data:")) {
                    const d = line.slice(5);
                    dataLines.push(d.startsWith(" ") ? d.slice(1) : d);
                }
            }
            const data = dataLines.join("\n");

            if (event === "done") return;
            if (event === "error") {
                let message = "The request failed";
                let code: string | undefined;
                try {
                    const parsed = JSON.parse(data);
                    message = parsed.message ?? message;
                    code = parsed.code;
                } catch {
                    /* keep the generic message */
                }
                throw new ApiError(500, message, code);
            }
            if (event === "message") {
                try {
                    handlers.onToken(JSON.parse(data) as string);
                } catch {
                    /* skip a malformed frame */
                }
            } else {
                handlers.onEvent?.(event, data);
            }
        }
    }
}
