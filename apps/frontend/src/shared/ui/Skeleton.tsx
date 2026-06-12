import { cn } from "./cn";

/**
 * A pulsing placeholder block. Use during first load only (keep loaded content
 * mounted on revalidation to avoid flicker).
 */
export function Skeleton({ className }: { className?: string }) {
    return <div className={cn("animate-pulse rounded bg-ink/10", className)} />;
}
