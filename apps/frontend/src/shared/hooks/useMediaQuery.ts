/**
 * @packageDocumentation Screen-size hooks. `useMediaQuery` subscribes to a CSS
 * media query. `useIsMobile` is the shared "below Tailwind's `sm` breakpoint"
 * check used to switch between desktop and mobile component layouts.
 */

import { useEffect, useState } from "react";

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
 * Whether the viewport is mobile-sized (below Tailwind's `md` = 768px). Matches
 * the `md:` breakpoint the player layout uses, so JS-driven swaps (toolbar,
 * panel-dock icons) stay in sync with the CSS layout.
 */
export function useIsMobile(): boolean {
    return useMediaQuery("(max-width: 767px)");
}
