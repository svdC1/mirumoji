/**
 * @packageDocumentation Compact, optionally interactive tag.
 */

import React from "react";
import { cn } from "./cn";

export interface ChipProps extends React.HTMLAttributes<HTMLSpanElement> {
    /** Render as a pressable element (adds hover affordance). */
    interactive?: boolean;
}

/**
 * A small rounded pill — used for the active-profile indicator, model tags, etc.
 */
export function Chip({ interactive = false, className, ...rest }: ChipProps) {
    return (
        <span
            className={cn(
                "inline-flex items-center gap-1.5 rounded-full border border-ink/10 bg-surface-2 px-3 py-1 text-sm text-ink-muted",
                interactive &&
                    "cursor-pointer transition-colors hover:border-ink/20 hover:text-ink",
                className
            )}
            {...rest}
        />
    );
}
