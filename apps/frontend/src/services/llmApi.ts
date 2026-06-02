/**
 * @packageDocumentation Client helpers for the provider-agnostic LLM API.
 */

import { apiFetch } from "../services/api";
import { ProviderStatus } from "../types/types";

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
