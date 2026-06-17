/**
 * @packageDocumentation Server-Sent Events client for the streaming LLM
 * endpoints (breakdown / explain). Uses `fetch` + a stream reader (an
 * `EventSource` can't POST a JSON body), parsing each `data:` frame as JSON
 * (the server JSON-encodes every chunk so multi-line markdown survives).
 */

import { API_BASE } from "@/shared/api/client";
import { ApiError } from "@/shared/api/errors";
import type { EnrichedJapaneseWord } from "@/shared/dict/types";

/** Handlers for a streamed LLM response. */
interface SSEHandlers {
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
 * @param {AbortSignal} [signal] Aborts the stream (e.g. dialog closed).
 * @returns {Promise<void>} Resolves at the `done` event.
 */
async function streamSSE(
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
        try {
            const parsed = JSON.parse(text);
            if (parsed?.error?.message) message = parsed.error.message;
        } catch {
            /* not the JSON error envelope */
        }
        throw new ApiError(res.status, message);
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

/**
 * Streams a word breakdown: the structured focus word first, then the
 * explanation token by token.
 *
 * @param {object} req The breakdown request.
 * @param {object} handlers `onFocus` (once) + `onToken` (per chunk).
 * @param {AbortSignal} [signal] Aborts the stream.
 * @returns {Promise<void>} Resolves when the explanation finishes.
 */
export async function streamBreakdown(
    req: { sentence: string; focus: string; model: string; sys_msg?: string; prompt?: string },
    handlers: {
        onFocus: (focus: EnrichedJapaneseWord | null) => void;
        onToken: (token: string) => void;
    },
    signal?: AbortSignal
): Promise<void> {
    await streamSSE(
        "llm/breakdown",
        req,
        {
            onToken: handlers.onToken,
            onEvent: (event, data) => {
                if (event !== "focus") return;
                try {
                    handlers.onFocus(JSON.parse(data) as EnrichedJapaneseWord);
                } catch {
                    handlers.onFocus(null);
                }
            },
        },
        signal
    );
}

/**
 * Streams an explanation of a whole sentence, token by token.
 *
 * @param {object} req The explanation request.
 * @param {object} handlers `onToken` (per chunk).
 * @param {AbortSignal} [signal] Aborts the stream.
 * @returns {Promise<void>} Resolves when the explanation finishes.
 */
export async function streamExplain(
    req: { sentence: string; model: string; sys_msg?: string; prompt?: string },
    handlers: { onToken: (token: string) => void },
    signal?: AbortSignal
): Promise<void> {
    await streamSSE("llm/explain_sentence", req, { onToken: handlers.onToken }, signal);
}
