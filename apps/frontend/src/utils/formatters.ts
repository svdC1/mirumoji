/**
 * @packageDocumentation This file contains formatter functions.
 */

/**
 * Converts a time string in the format "hh:mm:ss,ms" to seconds.
 *
 * @param {string} t The time string to convert.
 * @returns {number} The time in seconds.
 */
export const toSec = (t: string): number => {
    const [h, m, rest] = t.split(":");
    const [s, ms] = rest.split(",");
    return +h * 3600 + +m * 60 + +s + +ms / 1000;
};

/**
 * Converts a hex color string to an rgba color string.
 *
 * @param {string} hex The hex color string to convert.
 * @param {number} alpha The alpha value for the rgba color.
 * @returns {string} The rgba color string.
 */
export const hexToRgba = (hex: string, alpha: number): string => {
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
};
