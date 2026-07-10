/**
 * @packageDocumentation A single-select segmented control: a row of pill
 * options on a sunken track, the active one accented. Distinct from `Tabs`
 * (section navigation) and `Toggle` (a single on/off switch).
 */

import type { ReactNode } from "react";
import { cn } from "./cn";

export interface SegmentedOption<T extends string> {
    /** The value selected when this option is clicked. */
    value: T;
    /** The visible label. */
    label: ReactNode;
}

export interface SegmentedProps<T extends string> {
    /** The selectable options, rendered left to right. */
    options: SegmentedOption<T>[];
    /** The currently selected value. */
    value: T;
    /** Called with the newly selected value. */
    onChange: (value: T) => void;
    /** Optional class for the track wrapper. */
    className?: string;
}

/**
 * The Segmented component.
 *
 * @param {SegmentedProps} props The props.
 * @returns {JSX.Element} The segmented control.
 */
export function Segmented<T extends string>({
    options,
    value,
    onChange,
    className,
}: SegmentedProps<T>) {
    return (
        <div className={cn("flex gap-1 rounded-control bg-surface-2 p-1", className)}>
            {options.map((o) => (
                <button
                    key={o.value}
                    type="button"
                    onClick={() => onChange(o.value)}
                    className={cn(
                        "flex-1 rounded-control px-3 py-1.5 text-sm font-medium transition-colors",
                        value === o.value ? "bg-shu/15 text-shu" : "text-ink-muted hover:text-ink"
                    )}
                >
                    {o.label}
                </button>
            ))}
        </div>
    );
}
