/**
 * @packageDocumentation A popover of subtitle appearance controls (font size,
 * background opacity, vertical position, colors) + reset.
 */

import { useState } from "react";
import { SlidersHorizontal } from "lucide-react";
import { IconButton, Popover, Button, cn } from "@/shared/ui";
import { useSubtitleSettings } from "@/contexts/SubtitleSettingsContext";

function Range({
    label,
    value,
    min,
    max,
    step = 1,
    onChange,
}: {
    label: string;
    value: number;
    min: number;
    max: number;
    step?: number;
    onChange: (v: number) => void;
}) {
    return (
        <label className="block">
            <span className="mb-1 block text-2xs uppercase tracking-wide text-ink-faint">
                {label}
            </span>
            <input
                type="range"
                min={min}
                max={max}
                step={step}
                value={value}
                onChange={(e) => onChange(Number(e.target.value))}
                className="h-1 w-full cursor-pointer appearance-none rounded-full bg-ink/15 accent-shu"
            />
        </label>
    );
}

function ColorField({
    label,
    value,
    onChange,
}: {
    label: string;
    value: string;
    onChange: (v: string) => void;
}) {
    return (
        <label className="flex items-center justify-between gap-2">
            <span className="text-2xs uppercase tracking-wide text-ink-faint">{label}</span>
            <input
                type="color"
                value={value}
                onChange={(e) => onChange(e.target.value)}
                className="h-7 w-10 cursor-pointer rounded border border-ink/10 bg-transparent"
            />
        </label>
    );
}

/**
 * The SubtitleStylePopover component.
 *
 * @param {{ className?: string }} props Optional class for the trigger.
 * @returns {JSX.Element} The style controls trigger + popover.
 */
export function SubtitleStylePopover({ className }: { className?: string }) {
    const [open, setOpen] = useState(false);
    const { subtitleStyle, setSubtitleStyle, resetSubtitleStyle } = useSubtitleSettings();

    return (
        <div className={cn("relative", className)}>
            <IconButton label="Subtitle style" active={open} onClick={() => setOpen((v) => !v)}>
                <SlidersHorizontal size={18} />
            </IconButton>
            <Popover open={open} onClose={() => setOpen(false)} align="left" className="w-72 p-4">
                <div className="space-y-4">
                    <Range
                        label={`Font Size · ${subtitleStyle.fontSize}px`}
                        value={subtitleStyle.fontSize}
                        min={12}
                        max={48}
                        onChange={(fontSize) => setSubtitleStyle({ ...subtitleStyle, fontSize })}
                    />
                    <Range
                        label={`Background · ${(subtitleStyle.backgroundOpacity * 100).toFixed(0)}%`}
                        value={subtitleStyle.backgroundOpacity}
                        min={0}
                        max={1}
                        step={0.1}
                        onChange={(backgroundOpacity) =>
                            setSubtitleStyle({ ...subtitleStyle, backgroundOpacity })
                        }
                    />
                    <Range
                        label={`Position · ${subtitleStyle.position}%`}
                        value={subtitleStyle.position}
                        min={0}
                        max={90}
                        onChange={(position) => setSubtitleStyle({ ...subtitleStyle, position })}
                    />
                    <div className="space-y-2">
                        <ColorField
                            label="Text Color"
                            value={subtitleStyle.fontColor}
                            onChange={(fontColor) =>
                                setSubtitleStyle({ ...subtitleStyle, fontColor })
                            }
                        />
                        <ColorField
                            label="Background Color"
                            value={subtitleStyle.backgroundColor}
                            onChange={(backgroundColor) =>
                                setSubtitleStyle({ ...subtitleStyle, backgroundColor })
                            }
                        />
                    </div>
                    <Button
                        variant="secondary"
                        size="sm"
                        className="w-full"
                        onClick={resetSubtitleStyle}
                    >
                        Reset
                    </Button>
                </div>
            </Popover>
        </div>
    );
}
