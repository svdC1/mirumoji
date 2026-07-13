/**
 * @packageDocumentation Placeholder shown when there is no content.
 */

import React from "react";
import { cn } from "./cn";

export interface EmptyStateProps {
    icon?: React.ReactNode;
    title: string;
    description?: React.ReactNode;
    action?: React.ReactNode;
    className?: string;
}

/**
 * A centered placeholder for empty/no-data states.
 */
export function EmptyState({ icon, title, description, action, className }: EmptyStateProps) {
    return (
        <div
            className={cn(
                "flex flex-col items-center justify-center gap-3 px-6 py-12 text-center",
                className
            )}
        >
            {icon && <div className="text-ink-faint">{icon}</div>}
            <h3 className="font-display text-lg text-ink">{title}</h3>
            {description && <p className="max-w-sm text-sm text-ink-muted">{description}</p>}
            {action && <div className="mt-1">{action}</div>}
        </div>
    );
}
