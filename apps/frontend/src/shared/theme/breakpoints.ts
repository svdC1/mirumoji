/**
 * @packageDocumentation Shared responsive breakpoint definitions used by both
 * the Tailwind preset (as named screens) and the runtime media-query hooks, so
 * the CSS variants and the JS checks that mirror them never drift.
 */

/**
 * A landscape phone: landscape orientation with a short viewport. The subtitle
 * panel opts into its side-rail layout here (the `land:` Tailwind variant),
 * mirroring the desktop `lg:` rail so a short landscape height is not split
 * between a tiny video and a tiny cue list.
 */
export const LAND_SCREEN = "(orientation: landscape) and (max-height: 600px)";

/**
 * When the subtitle panel renders as a side rail: a desktop-width viewport
 * (Tailwind `lg` = 1024px) or a landscape phone. Matches `lg:` OR `land:` in
 * CSS, so JS-driven swaps (the dock icons) stay in sync with the layout.
 */
export const RAIL_SCREEN = `(min-width: 1024px), ${LAND_SCREEN}`;
