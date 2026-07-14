/**
 * @packageDocumentation Switch control.
 */

import { cn } from "./cn";

export interface ToggleProps {
    checked: boolean;
    onChange: (value: boolean) => void;
    label?: string;
    disabled?: boolean;
    id?: string;
}

/**
 * An accessible on/off switch.
 */
export function Toggle({ checked, onChange, label, disabled, id }: ToggleProps) {
    return (
        <button
            type="button"
            id={id}
            role="switch"
            aria-checked={checked}
            aria-label={label}
            disabled={disabled}
            onClick={() => onChange(!checked)}
            className={cn(
                "inline-flex h-6 w-11 shrink-0 items-center rounded-full transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-shu/60 disabled:opacity-50 disabled:pointer-events-none",
                checked ? "bg-shu" : "bg-ink/15"
            )}
        >
            <span
                className={cn(
                    "inline-block h-5 w-5 transform rounded-full bg-ink shadow-soft transition-transform",
                    checked ? "translate-x-5" : "translate-x-0.5"
                )}
            />
        </button>
    );
}
