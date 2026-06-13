import React, { useState } from "react";
import { ChevronDown } from "lucide-react";
import { cn } from "./cn";
import { Popover } from "./Popover";
import { useIsMobile } from "../hooks/useMediaQuery";

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
 * A controlled tab selector: an underline-style strip on desktop, and a compact
 * dropdown on mobile (so many tabs never overflow the viewport).
 */
export function Tabs({ items, value, onChange, className }: TabsProps) {
    const isMobile = useIsMobile();
    const [open, setOpen] = useState(false);

    if (isMobile) {
        const active = items.find((t) => t.id === value);
        return (
            <div className={cn("relative", className)}>
                <button
                    type="button"
                    aria-haspopup="listbox"
                    aria-expanded={open}
                    onClick={() => setOpen((v) => !v)}
                    className="flex w-full items-center justify-between rounded-control border border-ink/10 bg-surface-2 px-4 py-2.5 text-sm font-medium text-ink"
                >
                    {active?.label}
                    <ChevronDown
                        size={16}
                        className={cn("text-ink-faint transition-transform", open && "rotate-180")}
                    />
                </button>
                <Popover open={open} onClose={() => setOpen(false)} className="w-full p-1">
                    {items.map((t) => (
                        <button
                            key={t.id}
                            type="button"
                            role="option"
                            aria-selected={t.id === value}
                            onClick={() => {
                                onChange(t.id);
                                setOpen(false);
                            }}
                            className={cn(
                                "block w-full rounded-control px-3 py-2 text-left text-sm font-medium transition-colors",
                                t.id === value
                                    ? "bg-shu/15 text-shu"
                                    : "text-ink-muted hover:bg-ink/5 hover:text-ink"
                            )}
                        >
                            {t.label}
                        </button>
                    ))}
                </Popover>
            </div>
        );
    }

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
