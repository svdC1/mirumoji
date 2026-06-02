import React from "react";
import { cn } from "./cn";

export interface TabItem {
    id: string;
    label: React.ReactNode;
}

export interface TabsProps {
    items: TabItem[];
    value: string;
    onChange: (id: string) => void;
    className?: string;
}

/**
 * A horizontal, underline-style tab strip. Controlled via `value`/`onChange`.
 */
export function Tabs({ items, value, onChange, className }: TabsProps) {
    return (
        <div role="tablist" className={cn("flex gap-1 border-b border-ink/10", className)}>
            {items.map((t) => {
                const active = t.id === value;
                return (
                    <button
                        key={t.id}
                        role="tab"
                        aria-selected={active}
                        onClick={() => onChange(t.id)}
                        className={cn(
                            "relative -mb-px px-4 py-2.5 text-sm font-medium transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-shu/60",
                            active ? "text-ink" : "text-ink-faint hover:text-ink-muted"
                        )}
                    >
                        {t.label}
                        {active && (
                            <span className="absolute inset-x-2 -bottom-px h-0.5 rounded-full bg-shu" />
                        )}
                    </button>
                );
            })}
        </div>
    );
}
