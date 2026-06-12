/**
 * @packageDocumentation Time formatting helpers.
 */

/**
 * Converts an SRT time string `"hh:mm:ss,ms"` to seconds.
 *
 * @param {string} t The SRT timestamp.
 * @returns {number} Seconds.
 */
export const toSec = (t: string): number => {
    const [h, m, rest] = t.split(":");
    const [s, ms] = rest.split(",");
    return +h * 3600 + +m * 60 + +s + +ms / 1000;
};

/**
 * Formats seconds as `m:ss` (or `h:mm:ss`) for cue timestamps.
 *
 * @param {number} seconds The time in seconds.
 * @returns {string} A short clock string.
 */
export const formatClock = (seconds: number): string => {
    if (!isFinite(seconds) || seconds < 0) seconds = 0;
    const total = Math.floor(seconds);
    const h = Math.floor(total / 3600);
    const m = Math.floor((total % 3600) / 60);
    const s = total % 60;
    const mm = h > 0 ? String(m).padStart(2, "0") : String(m);
    const ss = String(s).padStart(2, "0");
    return h > 0 ? `${h}:${mm}:${ss}` : `${mm}:${ss}`;
};
