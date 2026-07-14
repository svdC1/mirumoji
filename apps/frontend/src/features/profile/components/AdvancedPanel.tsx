/**
 * @packageDocumentation The Advanced tab: profile-scoped operation settings,
 * split into Transcription (curated Whisper opts + clean-audio) and Conversion
 * sub-tabs. Each field carries a tooltip and a faded placeholder showing the
 * server default; an empty field is omitted from requests. A draft is edited
 * locally and committed with Save (or Reset to defaults).
 */

import { useEffect, useMemo, useState } from "react";
import { toast } from "react-hot-toast";
import {
    defaultOperationSettings,
    useOperationSettings,
    type OperationSettings,
} from "@/contexts/OperationSettingsContext";
import { Button, Card, InfoTip, Input, Label, Segmented, TextArea, Toggle } from "@/shared/ui";
import type { ConvertOpts, TranscribeOpts } from "@/shared/jobs/types";

type SubTab = "transcription" | "conversion";

// Hides the native number-input spin buttons (the white up/down arrows).
const SPINNER_OFF =
    "[appearance:textfield] [&::-webkit-inner-spin-button]:m-0 " +
    "[&::-webkit-inner-spin-button]:appearance-none " +
    "[&::-webkit-outer-spin-button]:m-0 [&::-webkit-outer-spin-button]:appearance-none";

/** A label row with an info tooltip in place of a descriptive hint. */
function InfoLabel({ label, info, htmlFor }: { label: string; info: string; htmlFor?: string }) {
    return (
        <div className="mb-1.5 flex items-center gap-1.5">
            <Label htmlFor={htmlFor} className="mb-0">
                {label}
            </Label>
            <InfoTip content={info} wide />
        </div>
    );
}

/** An optional numeric field that maps "" to `undefined` (server default). */
function NumField({
    label,
    info,
    value,
    onChange,
    step,
    placeholder,
}: {
    label: string;
    info: string;
    value: number | undefined;
    onChange: (value: number | undefined) => void;
    step?: number;
    placeholder?: string;
}) {
    return (
        <div>
            <InfoLabel label={label} info={info} />
            <Input
                type="number"
                step={step}
                value={value ?? ""}
                placeholder={placeholder}
                className={SPINNER_OFF}
                onChange={(e) => {
                    const raw = e.target.value;
                    const parsed = Number(raw);
                    onChange(raw === "" || Number.isNaN(parsed) ? undefined : parsed);
                }}
            />
        </div>
    );
}

/** A centered switch with a trailing label and an info tooltip. */
function ToggleRow({
    label,
    info,
    checked,
    onChange,
}: {
    label: string;
    info: string;
    checked: boolean;
    onChange: (value: boolean) => void;
}) {
    return (
        <div className="flex items-center gap-2.5">
            <Toggle checked={checked} onChange={onChange} label={label} />
            <span className="text-sm text-ink-muted">{label}</span>
            <InfoTip content={info} wide />
        </div>
    );
}

/**
 * The AdvancedPanel component.
 *
 * @returns {JSX.Element} The advanced settings panel.
 */
export function AdvancedPanel() {
    const { settings, replace } = useOperationSettings();
    const [subTab, setSubTab] = useState<SubTab>("transcription");
    const [draft, setDraft] = useState<OperationSettings>(settings);

    // Re-seed the draft when the committed settings change (e.g. profile switch).
    useEffect(() => {
        setDraft(settings);
    }, [settings]);

    const setT = (patch: Partial<TranscribeOpts>) =>
        setDraft((d) => ({ ...d, transcribe: { ...d.transcribe, ...patch } }));
    const setClean = (value: boolean) => setDraft((d) => ({ ...d, cleanAudio: value }));
    const setC = (patch: Partial<ConvertOpts>) =>
        setDraft((d) => ({ ...d, convert: { ...d.convert, ...patch } }));

    const dirty = useMemo(
        () => JSON.stringify(draft) !== JSON.stringify(settings),
        [draft, settings]
    );

    const onSave = () => {
        replace(draft);
        toast.success("Settings Saved");
    };

    const onReset = () => {
        const defaults = defaultOperationSettings();
        setDraft(defaults);
        replace(defaults);
        toast.success("Reset To Defaults");
    };

    const t = draft.transcribe;

    return (
        <Card className="space-y-5 p-6">
            <Segmented
                options={[
                    { value: "transcription", label: "Transcription" },
                    { value: "conversion", label: "Conversion" },
                ]}
                value={subTab}
                onChange={setSubTab}
            />

            {subTab === "transcription" ? (
                <>
                    <p className="text-sm text-ink-muted">
                        Whisper Options For Transcribe And Generate Subtitles. An Empty Field Uses
                        The Server Default
                    </p>

                    <div>
                        <InfoLabel label="Language" info="Spoken language Whisper transcribes in" />
                        <Input
                            value={t.language ?? ""}
                            placeholder="ja"
                            onChange={(e) => setT({ language: e.target.value || undefined })}
                        />
                    </div>

                    <div className="grid gap-4 sm:grid-cols-2">
                        <NumField
                            label="Beam Size"
                            info="Beam width for decoding (higher is more thorough, slower)"
                            value={t.beam_size}
                            step={1}
                            placeholder="5"
                            onChange={(v) => setT({ beam_size: v })}
                        />
                        <NumField
                            label="Best Of"
                            info="Number of candidates considered when sampling"
                            value={t.best_of}
                            step={1}
                            placeholder="5"
                            onChange={(v) => setT({ best_of: v })}
                        />
                        <NumField
                            label="Patience"
                            info="Beam-search patience factor"
                            value={t.patience}
                            step={0.1}
                            placeholder="1"
                            onChange={(v) => setT({ patience: v })}
                        />
                        <NumField
                            label="Length Penalty"
                            info="Exponential length penalty"
                            value={t.length_penalty}
                            step={0.1}
                            placeholder="1"
                            onChange={(v) => setT({ length_penalty: v })}
                        />
                        <NumField
                            label="Temperature"
                            info="Sampling temperature (0 is greedy)"
                            value={t.temperature}
                            step={0.1}
                            placeholder="0"
                            onChange={(v) => setT({ temperature: v })}
                        />
                        <NumField
                            label="Compression Ratio Threshold"
                            info="Treat output as failed above this gzip compression ratio"
                            value={t.compression_ratio_threshold}
                            step={0.1}
                            placeholder="2.0"
                            onChange={(v) => setT({ compression_ratio_threshold: v })}
                        />
                        <NumField
                            label="Log Prob Threshold"
                            info="Treat output as failed below this average log-probability"
                            value={t.log_prob_threshold}
                            step={0.1}
                            placeholder="-1.0"
                            onChange={(v) => setT({ log_prob_threshold: v })}
                        />
                        <NumField
                            label="No Speech Threshold"
                            info="Probability above which a segment is treated as silence"
                            value={t.no_speech_threshold}
                            step={0.05}
                            placeholder="0.3"
                            onChange={(v) => setT({ no_speech_threshold: v })}
                        />
                    </div>

                    <div>
                        <InfoLabel
                            label="Initial Prompt"
                            info="Optional text to bias the first transcription window"
                        />
                        <TextArea
                            className="min-h-[4rem]"
                            value={t.initial_prompt ?? ""}
                            placeholder="None"
                            onChange={(e) => setT({ initial_prompt: e.target.value || undefined })}
                        />
                    </div>

                    <div className="flex flex-wrap justify-center gap-x-8 gap-y-3 pt-1">
                        <ToggleRow
                            label="VAD Filter"
                            info="Skip non-speech with voice-activity detection"
                            checked={!!t.vad_filter}
                            onChange={(v) => setT({ vad_filter: v })}
                        />
                        <ToggleRow
                            label="Condition On Previous Text"
                            info="Feed prior text as context to the next window"
                            checked={!!t.condition_on_previous_text}
                            onChange={(v) => setT({ condition_on_previous_text: v })}
                        />
                        <ToggleRow
                            label="Clean Audio"
                            info="Apply a band-pass + loudness filter before transcribing"
                            checked={draft.cleanAudio}
                            onChange={setClean}
                        />
                    </div>
                </>
            ) : (
                <>
                    <p className="text-sm text-ink-muted">MP4 Conversion Output Settings</p>
                    <div>
                        <InfoLabel
                            label="Quality Preset"
                            info="Encoder speed against output quality, default is Balanced"
                        />
                        <Segmented
                            options={(["performance", "balanced", "quality"] as const).map((p) => ({
                                value: p,
                                label: p.charAt(0).toUpperCase() + p.slice(1),
                            }))}
                            value={draft.convert.preset ?? "balanced"}
                            onChange={(preset) => setC({ preset })}
                        />
                    </div>
                    <div className="grid gap-4 sm:grid-cols-2">
                        <div>
                            <InfoLabel
                                label="Resolution"
                                info="Maximum output size, width x height"
                            />
                            <Input
                                value={draft.convert.resolution ?? ""}
                                placeholder="1280x720"
                                onChange={(e) => setC({ resolution: e.target.value || undefined })}
                            />
                        </div>
                        <div>
                            <InfoLabel label="Target Bitrate" info="Video bitrate ceiling" />
                            <Input
                                value={draft.convert.target_bitrate ?? ""}
                                placeholder="2500k"
                                onChange={(e) =>
                                    setC({ target_bitrate: e.target.value || undefined })
                                }
                            />
                        </div>
                    </div>
                </>
            )}

            <div className="flex gap-2 border-t border-ink/10 pt-4">
                <Button onClick={onSave} disabled={!dirty}>
                    Save
                </Button>
                <Button variant="secondary" onClick={onReset}>
                    Reset<span className="hidden sm:inline">{" To Default"}</span>
                </Button>
            </div>
        </Card>
    );
}
