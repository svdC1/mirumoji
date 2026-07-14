/**
 * @packageDocumentation Screen-size hooks. `useMediaQuery` subscribes to a CSS
 * media query. `useIsMobile` is the shared "below Tailwind's `lg` breakpoint"
 * check used to switch between desktop and mobile component layouts.
 */

import { useEffect, useState } from "react";
import { RAIL_SCREEN } from "@/shared/theme/breakpoints";

/**
 * Subscribes to a media query and returns whether it currently matches,
 * updating on viewport changes.
 *
 * @param {string} query A CSS media query, e.g. `"(max-width: 639px)"`.
 * @returns {boolean} Whether the query currently matches.
 */
export function useMediaQuery(query: string): boolean {
    const [matches, setMatches] = useState(
        () => typeof window !== "undefined" && window.matchMedia(query).matches
    );

    useEffect(() => {
        const mql = window.matchMedia(query);
        const onChange = () => setMatches(mql.matches);
        onChange();
        mql.addEventListener("change", onChange);
        return () => mql.removeEventListener("change", onChange);
    }, [query]);

    return matches;
}

/**
 * Whether the viewport is mobile-sized (below Tailwind's `lg` = 1024px, i.e. up
 * to iPad Pro). Matches the `lg:` breakpoint the shell nav and player layout
 * use, so JS-driven swaps (toolbar, panel-dock icons) stay in sync with the CSS
 * layout.
 */
export function useIsMobile(): boolean {
    return useMediaQuery("(max-width: 1023px)");
}

/**
 * Whether the subtitle panel should render as a side rail rather than stacked:
 * a desktop-width viewport, or a landscape phone (short height). Matches the
 * `lg:`/`land:` rail classes so the JS-driven dock icons stay in sync with the
 * CSS layout. See `RAIL_SCREEN` in the shared breakpoints.
 */
export function useIsSubtitleRail(): boolean {
    return useMediaQuery(RAIL_SCREEN);
}
