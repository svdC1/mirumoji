/**
 * @packageDocumentation A selector for the token bundling mode (Words / Grammar
 * / Morphemes), wired to BundleSettingsContext. The choice is a global view
 * preference, so changing it re-tokenizes everywhere.
 */

import { useBundleSettings } from "@/contexts/BundleSettingsContext";
import { cn } from "@/shared/ui";
import type { BundleMode } from "@/shared/dict/types";

const OPTIONS: { value: BundleMode; label: string; hint: string }[] = [
    { value: "words", label: "Words", hint: "Whole Dictionary Words" },
    { value: "grammar", label: "Grammar", hint: "Split Into Grammar Blocks" },
    { value: "morphemes", label: "Morphemes", hint: "Every Raw Unit" },
];

/**
 * The BundleModeSelect component.
 *
 * @param {{ className?: string }} props Optional wrapper class.
 * @returns {JSX.Element} The bundling-mode option list.
 */
export function BundleModeSelect({ className }: { className?: string }) {
    const { mode, setMode } = useBundleSettings();
    const active = OPTIONS.find((o) => o.value === mode);

    return (
        <div className={className}>
            <span className="mb-1 block text-2xs uppercase tracking-wide text-ink-faint">
                Word Splitting
            </span>
            <div className="space-y-1">
                {OPTIONS.map((o) => (
                    <button
                        key={o.value}
                        type="button"
                        onClick={() => setMode(o.value)}
                        title={o.hint}
                        className={cn(
                            "flex w-full items-center gap-2 rounded-control px-3 py-2 text-left text-xs font-medium transition-colors",
                            mode === o.value
                                ? "bg-shu/15 text-shu"
                                : "text-ink-muted hover:bg-ink/5 hover:text-ink"
                        )}
                    >
                        <span
                            className={cn(
                                "h-1.5 w-1.5 shrink-0 rounded-full",
                                mode === o.value ? "bg-shu" : "bg-ink/20"
                            )}
                        />
                        {o.label}
                    </button>
                ))}
            </div>
            {active && <span className="mt-1.5 block text-2xs text-ink-faint">{active.hint}</span>}
        </div>
    );
}
