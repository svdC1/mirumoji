/**
 * @packageDocumentation The demo replacement for `@/shared/api/sse`, aliased in
 * only for `--mode demo`. Replays a recorded LLM stream (raw SSE body text)
 * through the same frame semantics as the real client, with a small per-token
 * delay for the live typewriter feel. An unrecorded stream degrades to a short
 * notice rather than a failed request.
 */

import { ApiError } from "@/shared/api/errors";
import type { SSEHandlers } from "@real/shared/api/sse";
import { lookupStream } from "./fixtures";

const delay = (ms: number): Promise<void> => new Promise((resolve) => setTimeout(resolve, ms));

/** Replays a recorded SSE stream, matching the real `streamSSE` signature. */
export async function streamSSE(
    url: string,
    body: unknown,
    handlers: SSEHandlers,
    signal?: AbortSignal
): Promise<void> {
    const raw = lookupStream(url, body);
    if (raw == null) {
        handlers.onToken("This Breakdown Is Not Part Of The Demo Sample");
        return;
    }

    for (const frame of raw.split("\n\n")) {
        if (signal?.aborted) return;

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
            await delay(16);
        } else {
            handlers.onEvent?.(event, data);
        }
    }
}
