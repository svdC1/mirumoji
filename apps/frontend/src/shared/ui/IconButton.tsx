/**
 * @packageDocumentation Icon-only button with an accessible label.
 */

import React from "react";
import { cn } from "./cn";

export interface IconButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
    /** Accessible label (also used as the native tooltip). */
    label: string;
    size?: "sm" | "md";
    active?: boolean;
}

/**
 * A square, icon-only button with a required accessible label.
 */
export function IconButton({
    label,
    size = "md",
    active = false,
    className,
    children,
    ...rest
}: IconButtonProps) {
    return (
        <button
            aria-label={label}
            title={label}
            aria-pressed={active}
            className={cn(
                "inline-flex items-center justify-center rounded-control transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-shu/60 disabled:opacity-50 disabled:pointer-events-none",
                active ? "bg-shu/15 text-shu" : "text-ink-muted hover:bg-ink/5 hover:text-ink",
                size === "sm" ? "h-8 w-8" : "h-10 w-10",
                className
            )}
            {...rest}
        >
            {children}
        </button>
    );
}
