/**
 * @packageDocumentation Provider-agnostic LLM types.
 */

import type { EnrichedJapaneseWord } from "@/shared/dict/types";

/**
 * A profile's LLM template (`/profiles/template`). `model` is a `provider:model`
 * selector (e.g. `"openai:gpt-4.1-mini"`).
 */
export interface LlmTemplate {
    id: string;
    sys_msg: string;
    prompt: string;
    model: string;
}

/** Availability of an LLM provider, from `/llm/providers`. */
export interface ProviderStatus {
    provider: string;
    available: boolean;
}

/** Response from `/llm/breakdown`: the focused word + its explanation. */
export interface BreakdownResponse {
    focus: EnrichedJapaneseWord | null;
    explanation: string;
}

/** Response from `/llm/explain_sentence`. */
export interface ExplanationResponse {
    explanation: string;
}

/** Response from `/llm/fix_srt`: the cleaned-up SRT content. */
export interface FixSrtResponse {
    srt: string;
}
