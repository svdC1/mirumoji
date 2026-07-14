/**
 * @packageDocumentation The demo replacement for `@/shared/dict/api`, aliased in
 * only for `--mode demo`. It re-exports the real dictionary client (whose calls
 * run through the demo `apiFetch`) and overrides only `dictAudioClipUrl`, the one
 * hardcoded `/api` literal that bypasses `API_BASE`, to be base-aware and point
 * at the bundled static audio clip.
 */

export * from "@real/shared/dict/api";

/** Base-aware URL of a bundled kanji pronunciation clip (static demo asset). */
export function dictAudioClipUrl(literal: string, clip: string): string {
    return `${import.meta.env.BASE_URL}api/dict-audio/${encodeURIComponent(literal)}-${encodeURIComponent(clip)}.mp3`;
}
