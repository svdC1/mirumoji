/**
 * @packageDocumentation The LLM Template tab. Two sub-tabs: "Word Breakdown"
 * (model + system message + prompt, used when clicking a word) and "Subtitle
 * Fix" (model + system message, used by the player's Fix SRT). One Save persists
 * the whole template.
 */

import { useEffect, useState } from "react";
import useSWR, { mutate } from "swr";
import { toast } from "react-hot-toast";
import { useProfile } from "@/contexts/ProfileContext";
import {
    apiGetTemplate,
    apiProviders,
    apiUpsertTemplate,
    apiDeleteTemplate,
    apiPreviewBreakdown,
    parseModel,
    formatModel,
} from "@/shared/llm/api";
import { toastApiError } from "@/shared/api/errors";
import { Button, Field, InfoTip, Label, TextArea, Card, Toggle, cn } from "@/shared/ui";
import type { LlmTemplate, ProviderStatus } from "@/shared/llm/types";
import {
    defaultSysMsg,
    defaultPrompt,
    defaultModel,
    defaultSrtSysMsg,
    defaultSrtModel,
} from "../constants";
import { ProviderModelPicker } from "./ProviderModelPicker";
import { NoProfile, PanelLoading } from "./panelStates";

type SubTab = "breakdown" | "srt";

// Sample values the live preview renders the current template against.
const PREVIEW_SENTENCE = "君のことが好きだ";
const PREVIEW_FOCUS = "好き";
const PREVIEW_CONTEXT = "ずっと言えなかった\n君のことが好きだ\n返事を聞かせて";

/**
 * The LlmTemplatePanel component.
 *
 * @returns {JSX.Element} The LLM template panel.
 */
export function LlmTemplatePanel() {
    const { profileId } = useProfile();
    const templateKey = profileId ? "profiles/template" : null;

    const { data: template, isLoading } = useSWR<LlmTemplate | null>(
        templateKey,
        () => apiGetTemplate(),
        { revalidateOnFocus: false, keepPreviousData: true }
    );
    const { data: providers } = useSWR<ProviderStatus[]>(
        profileId ? "llm/providers" : null,
        () => apiProviders(),
        { revalidateOnFocus: false, keepPreviousData: true }
    );

    const [subTab, setSubTab] = useState<SubTab>("breakdown");

    // Word-breakdown config.
    const [sysMsg, setSysMsg] = useState(defaultSysMsg);
    const [promptText, setPromptText] = useState(defaultPrompt);
    const dm = parseModel(defaultModel);
    const [provider, setProvider] = useState(dm.provider);
    const [modelName, setModelName] = useState(dm.name);

    // Subtitle-fix config.
    const [srtSysMsg, setSrtSysMsg] = useState(defaultSrtSysMsg);
    const dsm = parseModel(defaultSrtModel);
    const [srtProvider, setSrtProvider] = useState(dsm.provider);
    const [srtModelName, setSrtModelName] = useState(dsm.name);

    const [saving, setSaving] = useState(false);
    const [deleting, setDeleting] = useState(false);
    // Best-effort model validity, reported by each picker (default valid).
    const [breakdownValid, setBreakdownValid] = useState(true);
    const [srtValid, setSrtValid] = useState(true);

    // Live preview state.
    const [previewWithContext, setPreviewWithContext] = useState(true);
    const [preview, setPreview] = useState("");

    // Seed both sub-forms from the saved template, or from defaults when none.
    useEffect(() => {
        const src = template ?? {
            sys_msg: defaultSysMsg,
            prompt: defaultPrompt,
            model: defaultModel,
            srt_sys_msg: defaultSrtSysMsg,
            srt_model: defaultSrtModel,
        };
        const m = parseModel(src.model);
        setSysMsg(src.sys_msg);
        setPromptText(src.prompt);
        setProvider(m.provider);
        setModelName(m.name);

        const sm = parseModel(src.srt_model || defaultSrtModel);
        setSrtSysMsg(src.srt_sys_msg || defaultSrtSysMsg);
        setSrtProvider(sm.provider);
        setSrtModelName(sm.name);
    }, [template]);

    // Live preview: render the current template through the server (the same
    // renderer used for real breakdowns), debounced as the user types.
    useEffect(() => {
        if (!profileId || subTab !== "breakdown") return;
        const handle = window.setTimeout(() => {
            apiPreviewBreakdown({
                sentence: PREVIEW_SENTENCE,
                focus: PREVIEW_FOCUS,
                prompt: promptText,
                context: previewWithContext ? PREVIEW_CONTEXT : "",
            })
                .then(setPreview)
                .catch(() => setPreview(""));
        }, 300);
        return () => window.clearTimeout(handle);
    }, [profileId, subTab, promptText, previewWithContext]);

    if (!profileId) return <NoProfile what="manage your LLM template" />;
    if (isLoading && template === undefined) return <PanelLoading />;

    const persist = async (fields: {
        sys_msg: string;
        prompt: string;
        model: string;
        srt_sys_msg: string;
        srt_model: string;
    }) => {
        await apiUpsertTemplate(fields);
        mutate(templateKey);
    };

    const onSave = async () => {
        if (!breakdownValid) {
            setSubTab("breakdown");
            toast.error("Pick A Valid Word Breakdown Model");
            return;
        }
        if (!srtValid) {
            setSubTab("srt");
            toast.error("Pick A Valid Subtitle Fix Model");
            return;
        }
        setSaving(true);
        try {
            await persist({
                sys_msg: sysMsg,
                prompt: promptText,
                model: formatModel(provider, modelName),
                srt_sys_msg: srtSysMsg,
                srt_model: formatModel(srtProvider, srtModelName),
            });
            toast.success(template ? "Template Updated" : "Template Created");
        } catch (e) {
            toastApiError(e);
        } finally {
            setSaving(false);
        }
    };

    const onRevert = async () => {
        setSaving(true);
        try {
            await persist({
                sys_msg: defaultSysMsg,
                prompt: defaultPrompt,
                model: defaultModel,
                srt_sys_msg: defaultSrtSysMsg,
                srt_model: defaultSrtModel,
            });
            toast.success("Reverted To Default");
        } catch (e) {
            toastApiError(e);
        } finally {
            setSaving(false);
        }
    };

    const onDelete = async () => {
        setDeleting(true);
        try {
            await apiDeleteTemplate();
            mutate(templateKey, null, { revalidate: false });
            toast.success("Template Deleted");
        } catch (e) {
            toastApiError(e);
        } finally {
            setDeleting(false);
        }
    };

    const segBtn = (active: boolean) =>
        cn(
            "flex-1 rounded-control px-3 py-1.5 text-sm font-medium transition-colors",
            active ? "bg-shu/15 text-shu" : "text-ink-muted hover:text-ink"
        );

    return (
        <Card className="space-y-5 p-6">
            <div className="flex gap-1 rounded-control bg-surface-2 p-1">
                <button
                    className={segBtn(subTab === "breakdown")}
                    onClick={() => setSubTab("breakdown")}
                >
                    Word Breakdown
                </button>
                <button className={segBtn(subTab === "srt")} onClick={() => setSubTab("srt")}>
                    Subtitle Fix
                </button>
            </div>

            {subTab === "breakdown" ? (
                <>
                    <p className="text-sm text-ink-muted">Used When You Click A Word</p>
                    <ProviderModelPicker
                        provider={provider}
                        modelName={modelName}
                        providers={providers ?? []}
                        onProviderChange={setProvider}
                        onModelChange={setModelName}
                        onValidityChange={setBreakdownValid}
                    />
                    <Field label="System Message" htmlFor="sys-msg">
                        <TextArea
                            id="sys-msg"
                            value={sysMsg}
                            onChange={(e) => setSysMsg(e.target.value)}
                            className="min-h-[27rem] font-mono text-[0.8rem]"
                        />
                    </Field>
                    <div>
                        <div className="mb-1.5 flex items-center gap-1.5">
                            <Label htmlFor="prompt-text" className="mb-0">
                                Prompt
                            </Label>
                            <InfoTip
                                content={
                                    <div className="w-60 space-y-2.5 text-sm">
                                        <p className="text-2xs uppercase tracking-wide text-ink-faint">
                                            Filled in per lookup
                                        </p>
                                        <div className="space-y-1">
                                            <div className="flex items-baseline gap-2">
                                                <code className="shrink-0 rounded bg-ink/10 px-1 font-mono text-xs text-ink">
                                                    {"{sentence}"}
                                                </code>
                                                <span className="text-ink-muted">·</span>
                                                <span className="text-ink-muted">
                                                    Full Sentence
                                                </span>
                                            </div>
                                            <div className="flex items-baseline gap-2">
                                                <code className="shrink-0 rounded bg-ink/10 px-1 font-mono text-xs text-ink">
                                                    {"{focus}"}
                                                </code>
                                                <span className="text-ink-muted">·</span>
                                                <span className="text-ink-muted">Clicked Word</span>
                                            </div>
                                        </div>
                                        <p className="border-t border-ink/10 pt-2.5 text-2xs uppercase tracking-wide text-ink-faint">
                                            Context · Player Only
                                        </p>
                                        <div className="space-y-1">
                                            <p className="text-ink-muted">
                                                Wrap{" "}
                                                <code className="rounded bg-ink/10 px-1 font-mono text-xs text-ink">
                                                    {"{context}"}
                                                </code>{" "}
                                                In{" "}
                                                <code className="rounded bg-ink/10 px-1 font-mono text-xs text-ink">
                                                    {"{#context}...{/context}"}
                                                </code>{" "}
                                                To Include It Only When Present
                                            </p>
                                        </div>
                                    </div>
                                }
                            />
                        </div>
                        <TextArea
                            id="prompt-text"
                            value={promptText}
                            onChange={(e) => setPromptText(e.target.value)}
                            className="font-mono text-[0.8rem]"
                        />
                    </div>

                    <div>
                        <div className="mb-1.5 flex items-center justify-between gap-2">
                            <div className="flex items-center gap-1.5">
                                <Label className="mb-0">Preview</Label>
                                <InfoTip
                                    content="A live look at the prompt your template builds for an example word. Toggle With Context to see how it changes."
                                    wide
                                />
                            </div>
                            <div className="flex items-center gap-1.5 text-xs text-ink-muted">
                                <Toggle
                                    checked={previewWithContext}
                                    onChange={setPreviewWithContext}
                                    label="Preview with context"
                                />
                                <span>With Context</span>
                            </div>
                        </div>
                        <pre className="max-h-44 overflow-auto whitespace-pre-wrap rounded-control bg-surface-2 p-3 font-mono text-[0.8rem] text-ink-muted">
                            {preview || "..."}
                        </pre>
                    </div>
                </>
            ) : (
                <>
                    <p className="text-sm text-ink-muted">Used To Fix Subtitles</p>
                    <ProviderModelPicker
                        provider={srtProvider}
                        modelName={srtModelName}
                        providers={providers ?? []}
                        onProviderChange={setSrtProvider}
                        onModelChange={setSrtModelName}
                        onValidityChange={setSrtValid}
                    />
                    <Field label="System Message" htmlFor="srt-sys-msg">
                        <TextArea
                            id="srt-sys-msg"
                            value={srtSysMsg}
                            onChange={(e) => setSrtSysMsg(e.target.value)}
                            className="min-h-[27rem] font-mono text-[0.8rem]"
                        />
                    </Field>
                </>
            )}

            <div className="flex gap-2 border-t border-ink/10 pt-4">
                <Button onClick={onSave} loading={saving} disabled={deleting}>
                    {template ? "Update" : "Create"}
                    <span className="hidden sm:inline">{" Template"}</span>
                </Button>
                <Button variant="secondary" onClick={onRevert} disabled={saving || deleting}>
                    Revert<span className="hidden sm:inline">{" To Default"}</span>
                </Button>
                {template && (
                    <Button
                        variant="danger"
                        onClick={onDelete}
                        loading={deleting}
                        disabled={saving}
                    >
                        Delete
                    </Button>
                )}
            </div>
        </Card>
    );
}
