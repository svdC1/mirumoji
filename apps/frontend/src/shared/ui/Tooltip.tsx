import React from "react";
import { cn } from "./cn";

export interface TooltipProps {
    label: string;
    children: React.ReactNode;
    className?: string;
}

/**
 * A lightweight CSS hover/focus tooltip. Good enough for icon labels; not a
 * portal-based positioned tooltip.
 */
export function Tooltip({ label, children, className }: TooltipProps) {
    return (
        <span className={cn("group relative inline-flex", className)}>
            {children}
            <span
                role="tooltip"
                className="pointer-events-none absolute left-1/2 top-full z-50 mt-1.5 -translate-x-1/2 whitespace-nowrap rounded border border-ink/10 bg-surface-2 px-2 py-1 text-2xs text-ink-muted opacity-0 shadow-soft transition-opacity group-hover:opacity-100 group-focus-within:opacity-100"
            >
                {label}
            </span>
        </span>
    );
}
