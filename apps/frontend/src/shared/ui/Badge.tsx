/**
 * @packageDocumentation Small inline status and label pill.
 */

import React from "react";
import { cn } from "./cn";

export type BadgeTone = "neutral" | "accent" | "success" | "danger";

const TONES: Record<BadgeTone, string> = {
    neutral: "bg-ink/10 text-ink-muted",
    accent: "bg-shu/15 text-shu",
    success: "bg-matcha/15 text-matcha",
    danger: "bg-danger/15 text-danger",
};

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
    tone?: BadgeTone;
}

/**
 * A compact status label (uppercase, tracked).
 */
export function Badge({ tone = "neutral", className, ...rest }: BadgeProps) {
    return (
        <span
            className={cn(
                "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-2xs font-semibold uppercase tracking-wide",
                TONES[tone],
                className
            )}
            {...rest}
        />
    );
}
