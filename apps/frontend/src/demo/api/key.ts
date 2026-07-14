/**
 * @packageDocumentation The request-to-fixture key scheme shared by the demo
 * transport and `scripts/generate_demo_data.py`. Both sides MUST produce
 * byte-identical keys, so keep this in lockstep with the Python `key_of` mirror.
 *
 * GET/DELETE keys are `METHOD /api/<path>?<sorted-query>`. The handful of
 * body-keyed POSTs (tokenize batch + the LLM flows) also append a canonical,
 * sorted-key JSON of a per-endpoint field subset.
 */

/** POST paths whose fixture key includes a canonical subset of the request body. */
const BODY_KEYED: Record<string, string[]> = {
    "dict/tokenize": ["mode", "sentences"],
    "llm/breakdown": ["context", "focus", "sentence"],
    "llm/explain_sentence": ["sentence"],
    "llm/breakdown/preview": ["context", "focus", "prompt", "sentence"],
};

/** Recursively sorts object keys and drops `undefined`, so stringify is stable. */
function sortKeysDeep(value: unknown): unknown {
    if (Array.isArray(value)) return value.map(sortKeysDeep);
    if (value && typeof value === "object") {
        const out: Record<string, unknown> = {};
        for (const k of Object.keys(value as Record<string, unknown>).sort()) {
            const v = (value as Record<string, unknown>)[k];
            if (v !== undefined) out[k] = sortKeysDeep(v);
        }
        return out;
    }
    return value;
}

/**
 * Whitespace-free JSON with sorted keys, matching Python
 * `json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=False)`.
 */
function canonicalJson(value: unknown): string {
    return JSON.stringify(sortKeysDeep(value));
}

function safeParse(body: string): unknown {
    try {
        return JSON.parse(body);
    } catch {
        return null;
    }
}

/**
 * Computes the fixture key for a request in the `/api`-prefixed frontend form.
 *
 * @param {string} method The HTTP method.
 * @param {string} url The relative API path (as passed to `apiFetch`/`streamSSE`).
 * @param {unknown} [body] The request body (a JSON string from `apiFetch`, or a
 *     raw object from `streamSSE`); only used for the body-keyed POSTs.
 * @returns {string} The lookup key.
 */
export function keyOf(method: string, url: string, body?: unknown): string {
    const m = method.toUpperCase();
    const [rawPath, rawQuery = ""] = url.split("?");
    const path = rawPath.replace(/^\/+/, "");

    const query = [...new URLSearchParams(rawQuery).entries()]
        .sort(([a], [b]) => (a < b ? -1 : a > b ? 1 : 0))
        .map(([k, v]) => `${k}=${v}`)
        .join("&");

    let key = `${m} /api/${path}${query ? `?${query}` : ""}`;

    const fields = BODY_KEYED[path];
    if (fields && body != null) {
        const obj = typeof body === "string" ? safeParse(body) : body;
        const subset: Record<string, unknown> = {};
        for (const f of fields) {
            const v = (obj as Record<string, unknown> | null)?.[f];
            if (v !== undefined && v !== null) subset[f] = v;
        }
        key += `#${canonicalJson(subset)}`;
    }
    return key;
}
