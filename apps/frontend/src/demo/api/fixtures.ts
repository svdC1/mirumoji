/**
 * @packageDocumentation Loads the committed demo fixtures and decodes a recorded
 * response into the value `apiFetch` would return (a JSON value, text, or Blob).
 */

import fixturesJson from "../generated/fixtures.json";
import jobsJson from "../generated/jobs.json";
import sseJson from "../generated/sse.json";
import { keyOf } from "./key";

/** A recorded `apiFetch` response. */
export interface Fixture {
    status: number;
    contentType: string;
    /** A JSON value, or a string for text / SVG bodies. */
    body: unknown;
}

const fixtures = fixturesJson as unknown as Record<string, Fixture>;
const streams = sseJson as unknown as Record<string, string>;
const jobs = jobsJson as unknown as Record<string, unknown>;

/** Looks up a recorded response by request key. */
export function lookupFixture(method: string, url: string, body?: unknown): Fixture | undefined {
    return fixtures[keyOf(method, url, body)];
}

/** Looks up a recorded SSE stream (the raw response body text) by request key. */
export function lookupStream(url: string, body?: unknown): string | undefined {
    return streams[keyOf("POST", url, body)];
}

/** The canned terminal `result` for a job type (`generate_srt`, `transcribe`, ...). */
export function jobResult(type: string): unknown {
    return jobs[type];
}

/** Decodes a fixture into the value `apiFetch` returns for its content type. */
export function decodeFixture(fx: Fixture): unknown {
    if (fx.status === 204) return undefined;
    const ct = fx.contentType || "";
    if (ct.includes("application/json")) return fx.body;
    if (ct.startsWith("text/")) return fx.body as string;
    // Non-text bodies (an SVG stroke diagram, ...) are recorded as a string and
    // handed back as a Blob, exactly as the real apiFetch does for such types.
    return new Blob([fx.body as string], { type: ct || "application/octet-stream" });
}
