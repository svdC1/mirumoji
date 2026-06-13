/**
 * @packageDocumentation Parses an SRT file and pre-tokenizes every cue in one
 * batch request, so playback never tokenizes per-cue (no mid-video lag).
 */

import { useEffect, useState } from "react";
import SrtParser2 from "srt-parser-2";
import { apiTokenizeBatch } from "@/shared/dict/api";
import { useBundleSettings } from "@/contexts/BundleSettingsContext";
import { toSec } from "@/shared/format/time";
import type { Cue } from "../types";

export interface UseCuesResult {
    cues: Cue[];
    preparing: boolean;
}

/**
 * Parses + batch-tokenizes an SRT file into cues.
 *
 * @param {File | null} srt The subtitle file (or `null`).
 * @returns {UseCuesResult} The cues and a `preparing` flag (tokenizing).
 */
export function useCues(srt: File | null): UseCuesResult {
    const [cues, setCues] = useState<Cue[]>([]);
    const [preparing, setPreparing] = useState(false);
    const { mode } = useBundleSettings();

    useEffect(() => {
        let cancelled = false;
        (async () => {
            if (!srt) {
                setCues([]);
                return;
            }
            const txt = await srt.text();
            const parser = new SrtParser2();
            const parsed: Cue[] = parser.fromSrt(txt.trim()).map((c) => ({
                start: toSec(c.startTime),
                end: toSec(c.endTime),
                raw: c.text.replace(/<[^>]+>/g, "").trim(),
            }));

            // Clamp each cue's end to the next cue's start so a malformed/overlong
            // cue (e.g. an LLM-fix typo like 00:04:24 instead of 00:00:24) can't
            // bleed across the gaps that follow and "stick" on screen.
            for (let i = 0; i < parsed.length - 1; i++) {
                if (parsed[i].end > parsed[i + 1].start) {
                    parsed[i].end = parsed[i + 1].start;
                }
            }

            setPreparing(true);
            try {
                const wordsList = await apiTokenizeBatch(
                    parsed.map((c) => c.raw),
                    mode
                );
                if (cancelled) return;
                setCues(parsed.map((cue, i) => ({ ...cue, words: wordsList[i] })));
            } catch (err) {
                console.error("Failed to tokenize subtitles:", err);
                if (!cancelled) setCues(parsed); // fall back to raw text
            } finally {
                if (!cancelled) setPreparing(false);
            }
        })();
        return () => {
            cancelled = true;
        };
    }, [srt, mode]);

    return { cues, preparing };
}
