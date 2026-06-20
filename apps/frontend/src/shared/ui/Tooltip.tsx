import React from "react";
import { cn } from "./cn";

export interface TooltipProps {
    label: string;
    children: React.ReactNode;
    className?: string;
    /** Wrap the bubble to a readable width (for sentence-length explanations). */
    wide?: boolean;
}

/**
 * A lightweight CSS hover/focus tooltip. Good enough for icon labels; not a
 * portal-based positioned tooltip.
 */
export function Tooltip({ label, children, className, wide }: TooltipProps) {
    return (
        <span className={cn("group relative inline-flex", className)}>
            {children}
            <span
                role="tooltip"
                className={cn(
                    "pointer-events-none absolute left-1/2 top-full z-50 mt-1.5 -translate-x-1/2 rounded border border-ink/10 bg-surface-2 px-2 py-1 text-2xs text-ink-muted opacity-0 shadow-soft transition-opacity group-hover:opacity-100 group-focus-within:opacity-100",
                    wide ? "w-max max-w-[15rem] whitespace-normal text-center" : "whitespace-nowrap"
                )}
            >
                {label}
            </span>
        </span>
    );
}
