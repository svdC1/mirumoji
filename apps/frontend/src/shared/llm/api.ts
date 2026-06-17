/**
 * @packageDocumentation Client helpers for the provider-agnostic LLM API.
 */

import { apiFetch } from "@/shared/api/client";
import { ApiError } from "@/shared/api/errors";
import type { BreakdownResponse, ExplanationResponse, LlmTemplate, ProviderStatus } from "./types";

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
 * Explains the nuance of a focus word within a sentence (`/llm/breakdown`).
 *
 * @param {object} req The breakdown request.
 * @param {string} req.sentence The sentence containing the focus word.
 * @param {string} req.focus The word to explain in context.
 * @param {string} req.model The `provider:model` selector.
 * @param {string} [req.sys_msg] Optional custom system message.
 * @param {string} [req.prompt] Optional custom prompt (`{0}`=sentence, `{1}`=focus).
 * @returns {Promise<BreakdownResponse>} The focus word + explanation.
 */
export async function apiBreakdown(req: {
    sentence: string;
    focus: string;
    model: string;
    sys_msg?: string;
    prompt?: string;
}): Promise<BreakdownResponse> {
    return apiFetch<BreakdownResponse>("llm/breakdown", {
        method: "POST",
        body: JSON.stringify(req),
    });
}

/**
 * Explains a whole sentence, without a focus word (`/llm/explain_sentence`).
 *
 * @param {object} req The explanation request.
 * @param {string} req.sentence The sentence to explain.
 * @param {string} req.model The `provider:model` selector.
 * @param {string} [req.sys_msg] Optional custom system message.
 * @param {string} [req.prompt] Optional custom prompt (`{0}`=sentence).
 * @returns {Promise<ExplanationResponse>} The explanation.
 */
export async function apiExplainSentence(req: {
    sentence: string;
    model: string;
    sys_msg?: string;
    prompt?: string;
}): Promise<ExplanationResponse> {
    return apiFetch<ExplanationResponse>("llm/explain_sentence", {
        method: "POST",
        body: JSON.stringify(req),
    });
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
