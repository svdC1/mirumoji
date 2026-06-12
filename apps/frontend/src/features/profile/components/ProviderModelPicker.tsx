/**
 * @packageDocumentation Provider + model selector. A custom logo-capable
 * dropdown (a native <select> can't render images) listing providers from
 * /llm/providers with their availability, plus a free model-name input.
 */

import { useState } from "react";
import { ChevronDown, Check } from "lucide-react";
import { Field, Input, Label, Popover, controlClasses, cn } from "@/shared/ui";
import { ProviderLogo } from "@/shared/brand/ProviderLogo";
import type { ProviderStatus } from "@/shared/llm/types";

export interface ProviderModelPickerProps {
    provider: string;
    modelName: string;
    providers: ProviderStatus[];
    onProviderChange: (provider: string) => void;
    onModelChange: (model: string) => void;
}

/**
 * The ProviderModelPicker component.
 *
 * @param {ProviderModelPickerProps} props The props.
 * @returns {JSX.Element} The provider dropdown + model input.
 */
export function ProviderModelPicker({
    provider,
    modelName,
    providers,
    onProviderChange,
    onModelChange,
}: ProviderModelPickerProps) {
    const [open, setOpen] = useState(false);

    // Always include the current provider so a saved (possibly unconfigured)
    // selection stays visible.
    const options: ProviderStatus[] = providers.some((p) => p.provider === provider)
        ? providers
        : [{ provider, available: true }, ...providers];

    return (
        <div className="grid gap-4 sm:grid-cols-2">
            <div>
                <Label htmlFor="provider-picker">Provider</Label>
                <div className="relative">
                    <button
                        id="provider-picker"
                        type="button"
                        onClick={() => setOpen((v) => !v)}
                        className={cn(controlClasses, "flex items-center justify-between gap-2")}
                    >
                        <span className="flex min-w-0 items-center gap-2">
                            <ProviderLogo provider={provider} size={18} />
                            <span className="truncate">{provider}</span>
                        </span>
                        <ChevronDown size={16} className="shrink-0 text-ink-faint" />
                    </button>
                    <Popover open={open} onClose={() => setOpen(false)} className="w-full p-1">
                        <ul className="max-h-60 overflow-y-auto">
                            {options.map((p) => (
                                <li key={p.provider}>
                                    <button
                                        type="button"
                                        disabled={!p.available}
                                        onClick={() => {
                                            onProviderChange(p.provider);
                                            setOpen(false);
                                        }}
                                        className={cn(
                                            "flex w-full items-center gap-2 rounded-control px-2 py-1.5 text-left text-sm transition-colors",
                                            p.available
                                                ? "text-ink hover:bg-ink/5"
                                                : "cursor-not-allowed text-ink-faint"
                                        )}
                                    >
                                        <ProviderLogo provider={p.provider} size={18} />
                                        <span className="flex-1 truncate">{p.provider}</span>
                                        {!p.available && (
                                            <span className="text-2xs text-ink-faint">
                                                Not Configured
                                            </span>
                                        )}
                                        {p.provider === provider && (
                                            <Check size={15} className="text-shu" />
                                        )}
                                    </button>
                                </li>
                            ))}
                        </ul>
                    </Popover>
                </div>
            </div>

            <Field label="Model" htmlFor="model-name">
                <Input
                    id="model-name"
                    value={modelName}
                    onChange={(e) => onModelChange(e.target.value)}
                    placeholder="e.g. gpt-4.1-mini"
                />
            </Field>
        </div>
    );
}
