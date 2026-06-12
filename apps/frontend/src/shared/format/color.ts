/**
 * @packageDocumentation Color formatting helpers.
 */

/**
 * Converts a `#rrggbb` hex color to an `rgba()` string.
 *
 * @param {string} hex The hex color.
 * @param {number} alpha The alpha channel (0–1).
 * @returns {string} An `rgba(...)` string.
 */
export const hexToRgba = (hex: string, alpha: number): string => {
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
};
