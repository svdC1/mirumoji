import { Check } from "lucide-react";
import { cn } from "./cn";

export interface CheckboxProps {
    checked: boolean;
    onChange: (value: boolean) => void;
    label?: string;
    className?: string;
}

/**
 * A themed checkbox (no native white box): a hairline square that fills with the
 * Shu accent and shows a check when selected.
 */
export function Checkbox({ checked, onChange, label, className }: CheckboxProps) {
    return (
        <button
            type="button"
            role="checkbox"
            aria-checked={checked}
            aria-label={label}
            onClick={() => onChange(!checked)}
            className={cn(
                "grid h-4 w-4 shrink-0 place-items-center rounded border transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-shu/60",
                checked
                    ? "border-shu bg-shu text-bg"
                    : "border-ink/25 bg-surface-2 hover:border-ink/45",
                className
            )}
        >
            {checked && <Check size={12} strokeWidth={3} />}
        </button>
    );
}
