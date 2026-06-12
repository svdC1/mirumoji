/**
 * @packageDocumentation A small provider mark for the LLM provider picker /
 * model chips. Providers with a brand SVG render it as a CSS mask tinted to the
 * surrounding text color (so the monochrome marks stay visible on the dark
 * theme and adopt disabled/active text colors); other providers fall back to a
 * brand-tinted monogram or a generic icon.
 */

import { HardDrive, Sparkles } from "lucide-react";
import { cn } from "@/shared/ui";
import openaiUrl from "@/assets/brands/openai.svg";
import anthropicUrl from "@/assets/brands/anthropic.svg";
import googleUrl from "@/assets/brands/google.svg";

// Provider id (substring) -> brand SVG. `gemini` maps to Google's mark.
const LOGOS: Record<string, string> = {
    openai: openaiUrl,
    anthropic: anthropicUrl,
    gemini: googleUrl,
    google: googleUrl,
};

// Providers without an SVG get a brand-tinted monogram.
const MONOGRAMS: Record<string, { label: string; className: string }> = {
    mistral: { label: "M", className: "bg-[#fa5310]/20 text-[#fb7a4a]" },
};

export interface ProviderLogoProps {
    provider: string;
    size?: number;
    className?: string;
}

/**
 * The ProviderLogo component.
 *
 * @param {ProviderLogoProps} props The props.
 * @returns {JSX.Element} The provider mark.
 */
export function ProviderLogo({ provider, size = 18, className }: ProviderLogoProps) {
    const key = provider.toLowerCase();
    const dim = { width: size, height: size };

    const logoUrl = Object.keys(LOGOS).find((k) => key.includes(k));
    if (logoUrl) {
        const url = LOGOS[logoUrl];
        return (
            <span
                aria-hidden
                className={cn("inline-block shrink-0 bg-current", className)}
                style={{
                    ...dim,
                    maskImage: `url("${url}")`,
                    WebkitMaskImage: `url("${url}")`,
                    maskRepeat: "no-repeat",
                    WebkitMaskRepeat: "no-repeat",
                    maskPosition: "center",
                    WebkitMaskPosition: "center",
                    maskSize: "contain",
                    WebkitMaskSize: "contain",
                }}
            />
        );
    }

    const base =
        "inline-flex shrink-0 items-center justify-center rounded-[0.35em] font-display font-semibold leading-none";

    const monogramKey = Object.keys(MONOGRAMS).find((k) => key.includes(k));
    if (monogramKey) {
        const m = MONOGRAMS[monogramKey];
        return (
            <span
                style={{ ...dim, fontSize: size * 0.46 }}
                className={cn(base, m.className, className)}
            >
                {m.label}
            </span>
        );
    }

    const Icon = key.includes("local") ? HardDrive : Sparkles;
    return (
        <span style={dim} className={cn(base, "bg-ink/10 text-ink-muted", className)}>
            <Icon size={Math.round(size * 0.6)} />
        </span>
    );
}
