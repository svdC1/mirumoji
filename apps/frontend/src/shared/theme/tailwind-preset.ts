/**
 * @packageDocumentation
 * Tailwind preset that surfaces the "Sumi & Shu" design tokens
 * (see tokens.css) as named utilities, e.g. `bg-bg`, `text-ink-muted`,
 * `border-ink/10`, `bg-shu/20`, `font-display`, `rounded-card`.
 *
 * Colors map to `rgb(var(--token) / <alpha-value>)` so Tailwind's opacity
 * modifiers (`/10`, `/50`, ...) work against the CSS-variable channels.
 */
import type { Config } from "tailwindcss";

import { LAND_SCREEN } from "./breakpoints";

const c = (v: string) => `rgb(var(${v}) / <alpha-value>)`;

const preset: Partial<Config> = {
    theme: {
        extend: {
            screens: {
                // Additive named screen: a landscape phone. Only the player's
                // subtitle-panel layout opts into it (`land:` alongside the
                // existing `lg:` rail classes), so no other breakpoint changes.
                land: { raw: LAND_SCREEN },
            },
            colors: {
                bg: c("--bg"),
                surface: {
                    DEFAULT: c("--surface"),
                    2: c("--surface-2"),
                },
                ink: {
                    DEFAULT: c("--ink"),
                    muted: c("--ink-muted"),
                    faint: c("--ink-faint"),
                },
                shu: {
                    DEFAULT: c("--shu"),
                    soft: c("--shu-soft"),
                },
                ai: c("--ai"),
                matcha: c("--matcha"),
                danger: c("--danger"),
            },
            fontFamily: {
                display: ['"Newsreader"', "Georgia", "serif"],
                sans: ['"Hanken Grotesk"', "system-ui", "sans-serif"],
                jp: ['"Noto Serif JP"', "serif"],
            },
            fontSize: {
                "2xs": ["0.6875rem", { lineHeight: "1rem" }],
            },
            borderRadius: {
                card: "var(--radius-card)",
                control: "var(--radius-control)",
            },
            boxShadow: {
                soft: "0 1px 2px rgb(0 0 0 / 0.3), 0 8px 24px -12px rgb(0 0 0 / 0.5)",
                lift: "0 2px 4px rgb(0 0 0 / 0.35), 0 16px 40px -16px rgb(0 0 0 / 0.6)",
            },
        },
    },
};

export default preset;
