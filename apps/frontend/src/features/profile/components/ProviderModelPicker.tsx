/**
 * @packageDocumentation Provider + model selector. A custom logo-capable
 * dropdown (a native <select> can't render images) listing providers from
 * /llm/providers with their availability, plus a model combobox that filters the
 * provider's /llm/models catalogue as you type (local stays free-text).
 * `onValidityChange` reports whether the model is in the catalogue, for
 * best-effort save validation.
 */

import { useEffect, useState } from "react";
import { ChevronDown, Check } from "lucide-react";
import { Field, Input, Label, Popover, controlClasses, cn } from "@/shared/ui";
import { apiListModels } from "@/shared/llm/api";
import { ProviderLogo } from "@/shared/brand/ProviderLogo";
import type { ProviderStatus } from "@/shared/llm/types";

export interface ProviderModelPickerProps {
    provider: string;
    modelName: string;
    providers: ProviderStatus[];
    onProviderChange: (provider: string) => void;
    onModelChange: (model: string) => void;
    onValidityChange?: (valid: boolean) => void;
}

type ModelsState = "loading" | "ready" | "error";

/**
 * The ProviderModelPicker component.
 *
 * @param {ProviderModelPickerProps} props The props.
 * @returns {JSX.Element} The provider dropdown + model combobox.
 */
export function ProviderModelPicker({
    provider,
    modelName,
    providers,
    onProviderChange,
    onModelChange,
    onValidityChange,
}: ProviderModelPickerProps) {
    const [open, setOpen] = useState(false);
    const [modelOpen, setModelOpen] = useState(false);
    const [models, setModels] = useState<string[]>([]);
    const [modelsState, setModelsState] = useState<ModelsState>("loading");

    const providersLoaded = providers.length > 0;
    const available = providers.find((p) => p.provider === provider)?.available ?? false;
    const isLocal = provider === "local";

    const filteredModels = models.filter((m) => m.toLowerCase().includes(modelName.toLowerCase()));

    // Best-effort: a model is valid unless we have a catalogue that omits it.
    const valid = isLocal || modelsState !== "ready" || models.includes(modelName);

    // Fetch the provider's catalogue (cloud only); local stays free-text.
    useEffect(() => {
        if (isLocal) return;
        if (!providersLoaded) {
            setModelsState("loading");
            return;
        }
        if (!available) {
            setModels([]);
            setModelsState("error");
            return;
        }
        let cancelled = false;
        setModelsState("loading");
        apiListModels(provider)
            .then((m) => {
                if (cancelled) return;
                setModels(m);
                setModelsState("ready");
            })
            .catch(() => {
                if (cancelled) return;
                setModels([]);
                setModelsState("error");
            });
        return () => {
            cancelled = true;
        };
    }, [provider, available, providersLoaded, isLocal]);

    useEffect(() => {
        onValidityChange?.(valid);
    }, [valid, onValidityChange]);

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

            {isLocal ? (
                // A local server's model is whatever it serves; free-text.
                <Field label="Model" htmlFor="model-name">
                    <Input
                        id="model-name"
                        value={modelName}
                        onChange={(e) => onModelChange(e.target.value)}
                        placeholder="e.g. my-local-model"
                    />
                </Field>
            ) : (
                // Combobox: filter the provider's catalogue as you type.
                <div>
                    <Label htmlFor="model-name">Model</Label>
                    <div className="relative">
                        <Input
                            id="model-name"
                            value={modelName}
                            onChange={(e) => {
                                onModelChange(e.target.value);
                                setModelOpen(true);
                            }}
                            onFocus={() => setModelOpen(true)}
                            placeholder="Search models …"
                            className={cn("pr-9", !valid && "border-danger")}
                        />
                        <button
                            type="button"
                            aria-label="Toggle model list"
                            onClick={() => setModelOpen((v) => !v)}
                            className="absolute right-2 top-1/2 -translate-y-1/2 text-ink-faint transition-colors hover:text-ink"
                        >
                            <ChevronDown size={16} />
                        </button>
                        <Popover
                            open={modelOpen}
                            onClose={() => setModelOpen(false)}
                            className="w-full p-1"
                        >
                            {modelsState === "loading" ? (
                                <p className="px-2 py-1.5 text-sm text-ink-faint">Loading …</p>
                            ) : modelsState === "error" ? (
                                <p className="px-2 py-1.5 text-sm text-ink-faint">
                                    Failed To Fetch Models
                                </p>
                            ) : filteredModels.length === 0 ? (
                                <p className="px-2 py-1.5 text-sm text-ink-faint">
                                    No Matches Found
                                </p>
                            ) : (
                                <ul className="max-h-60 overflow-y-auto">
                                    {filteredModels.map((m) => (
                                        <li key={m}>
                                            <button
                                                type="button"
                                                onClick={() => {
                                                    onModelChange(m);
                                                    setModelOpen(false);
                                                }}
                                                className="flex w-full items-center gap-2 rounded-control px-2 py-1.5 text-left text-sm text-ink transition-colors hover:bg-ink/5"
                                            >
                                                <span className="flex-1 truncate">{m}</span>
                                                {m === modelName && (
                                                    <Check size={15} className="text-shu" />
                                                )}
                                            </button>
                                        </li>
                                    ))}
                                </ul>
                            )}
                        </Popover>
                    </div>
                </div>
            )}
        </div>
    );
}
