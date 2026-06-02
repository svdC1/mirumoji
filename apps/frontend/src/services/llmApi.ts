/**
 * @packageDocumentation Client helpers for the provider-agnostic LLM API.
 */

import { apiFetch } from "../services/api";
import {
    ApiError,
    BreakdownResponse,
    ExplanationResponse,
    LlmTemplate,
    ProviderStatus,
} from "../types/types";

/**
 * Lists which LLM providers are usable in this deployment.
 *
 * @returns {Promise<ProviderStatus[]>} A promise that resolves to the
 *     provider availability list from `/llm/providers`.
 */
export async function apiProviders(): Promise<ProviderStatus[]> {
    const res = await apiFetch<{ providers: ProviderStatus[] }>("llm/providers", { method: "GET" });
    return res.providers;
}

/**
 * Fetches the active profile's LLM template, or `null` when none is set.
 *
 * The model selector (and optional sys_msg/prompt) for LLM calls live here, so
 * callers use this to discover whether LLM features are configured.
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
 * Explains the nuance of a focus word within a sentence (`/llm/breakdown`).
 *
 * @param {object} req The breakdown request.
 * @param {string} req.sentence The sentence containing the focus word.
 * @param {string} req.focus The word to explain in context.
 * @param {string} req.model The `provider:model` selector.
 * @param {string} [req.sys_msg] Optional custom system message.
 * @param {string} [req.prompt] Optional custom prompt template (`{0}`=sentence,
 *     `{1}`=focus).
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
 * @param {string} [req.prompt] Optional custom prompt template (`{0}`=sentence).
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
 * Splits a `provider:model` selector into its parts (provider defaults to
 * `openai` when no prefix is present).
 *
 * @param {string} model The `provider:model` selector.
 * @returns {{ provider: string; name: string }} The provider and model name.
 */
export function parseModel(model: string): { provider: string; name: string } {
    const idx = model.indexOf(":");
    if (idx === -1) return { provider: "openai", name: model };
    return { provider: model.slice(0, idx), name: model.slice(idx + 1) };
}

/**
 * Joins a provider and model name into a `provider:model` selector.
 *
 * @param {string} provider The provider id (e.g. `openai`).
 * @param {string} name The model name (e.g. `gpt-4.1-mini`).
 * @returns {string} The combined `provider:model` selector.
 */
export function formatModel(provider: string, name: string): string {
    return `${provider}:${name}`;
}
