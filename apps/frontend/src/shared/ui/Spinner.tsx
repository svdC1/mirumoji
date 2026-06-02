import { cn } from "./cn";

/**
 * A minimal spinning loader that inherits `currentColor`.
 */
export function Spinner({ className }: { className?: string }) {
    return (
        <span
            aria-hidden
            className={cn(
                "inline-block animate-spin rounded-full border-2 border-current border-t-transparent",
                className ?? "h-4 w-4"
            )}
        />
    );
}
