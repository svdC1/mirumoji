/**
 * @packageDocumentation Client helpers for the provider-agnostic LLM API.
 */

import { apiFetch } from "@/shared/api/client";
import { ApiError } from "@/shared/api/errors";
import { streamSSE } from "@/shared/api/sse";
import type { EnrichedJapaneseWord } from "@/shared/dict/types";
import type { LlmTemplate, ProviderStatus } from "./types";

/**
 * Lists which LLM providers are usable in this deployment (`/llm/providers`).
 *
 * @returns {Promise<ProviderStatus[]>} The provider availability list.
 */
export async function apiProviders(): Promise<ProviderStatus[]> {
    const res = await apiFetch<{ providers: ProviderStatus[] }>("llm/providers", { method: "GET" });
    return res.providers;
}

/**
 * Lists the available models for a provider (`/llm/models`).
 *
 * @param {string} provider The provider id.
 * @returns {Promise<string[]>} The available model ids.
 */
export async function apiListModels(provider: string): Promise<string[]> {
    const res = await apiFetch<{ models: string[] }>(
        `llm/models?provider=${encodeURIComponent(provider)}`,
        { method: "GET" }
    );
    return res.models;
}

/**
 * Fetches the active profile's LLM template, or `null` when none is set.
 *
 * @returns {Promise<LlmTemplate | null>} The template, or `null` on 404.
 */
export async function apiGetTemplate(): Promise<LlmTemplate | null> {
    try {
        return await apiFetch<LlmTemplate>("profiles/template", { method: "GET" });
    } catch (err) {
        if (err instanceof ApiError && err.status === 404) return null;
        throw err;
    }
}

/**
 * Creates or updates the active profile's LLM template (`POST /profiles/template`).
 *
 * @param {object} req The template fields.
 * @param {string} req.sys_msg The system message.
 * @param {string} req.prompt The prompt template.
 * @param {string} req.model The `provider:model` selector.
 * @returns {Promise<LlmTemplate>} The saved template.
 */
export async function apiUpsertTemplate(req: {
    sys_msg: string;
    prompt: string;
    model: string;
    srt_sys_msg?: string;
    srt_model?: string;
}): Promise<LlmTemplate> {
    return apiFetch<LlmTemplate>("profiles/template", {
        method: "POST",
        body: JSON.stringify(req),
    });
}

/**
 * Deletes the active profile's LLM template (`DELETE /profiles/template`).
 *
 * @returns {Promise<void>} Resolves when deleted.
 */
export async function apiDeleteTemplate(): Promise<void> {
    await apiFetch("profiles/template", { method: "DELETE" });
}

/**
 * Streams a word breakdown (`/llm/breakdown`): the structured focus word first,
 * then the explanation token by token.
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
 * Streams an explanation of a whole sentence (`/llm/explain_sentence`), token
 * by token.
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

/**
 * Splits a `provider:model` selector (provider defaults to `openai`).
 *
 * @param {string} model The selector.
 * @returns {{ provider: string; name: string }} Provider + model name.
 */
export function parseModel(model: string): { provider: string; name: string } {
    const idx = model.indexOf(":");
    if (idx === -1) return { provider: "openai", name: model };
    return { provider: model.slice(0, idx), name: model.slice(idx + 1) };
}

/**
 * Joins a provider + model name into a `provider:model` selector.
 *
 * @param {string} provider The provider id.
 * @param {string} name The model name.
 * @returns {string} The combined selector.
 */
export function formatModel(provider: string, name: string): string {
    return `${provider}:${name}`;
}
