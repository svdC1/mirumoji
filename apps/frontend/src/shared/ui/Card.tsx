import React from "react";
import { cn } from "./cn";

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
    /** Slightly raised surface with a stronger shadow. */
    elevated?: boolean;
}

/**
 * A surface container with a hairline border and the theme radius.
 */
export function Card({ elevated = false, className, ...rest }: CardProps) {
    return (
        <div
            className={cn(
                "rounded-card border border-ink/10 bg-surface",
                elevated ? "shadow-lift" : "shadow-soft",
                className
            )}
            {...rest}
        />
    );
}
