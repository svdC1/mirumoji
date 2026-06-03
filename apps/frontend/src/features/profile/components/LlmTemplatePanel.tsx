/**
 * @packageDocumentation The LLM Template tab: provider/model picker + system
 * message + prompt, with save / revert-to-default / delete.
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
    parseModel,
    formatModel,
} from "@/shared/llm/api";
import { toastApiError } from "@/shared/api/errors";
import { Button, Field, Label, TextArea, Card, Popover } from "@/shared/ui";
import type { LlmTemplate, ProviderStatus } from "@/shared/llm/types";
import { defaultSysMsg, defaultPrompt, defaultModel } from "../constants";
import { ProviderModelPicker } from "./ProviderModelPicker";
import { NoProfile, PanelLoading } from "./panelStates";

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

    const [sysMsg, setSysMsg] = useState(defaultSysMsg);
    const [promptText, setPromptText] = useState(defaultPrompt);
    const seededModel = parseModel(defaultModel);
    const [provider, setProvider] = useState(seededModel.provider);
    const [modelName, setModelName] = useState(seededModel.name);
    const [saving, setSaving] = useState(false);
    const [deleting, setDeleting] = useState(false);
    const [helpOpen, setHelpOpen] = useState(false);

    // Seed the form from the saved template, or from defaults when none exists.
    useEffect(() => {
        const src = template
            ? { sys_msg: template.sys_msg, prompt: template.prompt, model: template.model }
            : { sys_msg: defaultSysMsg, prompt: defaultPrompt, model: defaultModel };
        const m = parseModel(src.model);
        setSysMsg(src.sys_msg);
        setPromptText(src.prompt);
        setProvider(m.provider);
        setModelName(m.name);
    }, [template]);

    if (!profileId) return <NoProfile what="manage your LLM template" />;
    if (isLoading && template === undefined) return <PanelLoading />;

    const persist = async (fields: { sys_msg: string; prompt: string; model: string }) => {
        await apiUpsertTemplate(fields);
        mutate(templateKey);
    };

    const onSave = async () => {
        setSaving(true);
        try {
            await persist({
                sys_msg: sysMsg,
                prompt: promptText,
                model: formatModel(provider, modelName),
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
            await persist({ sys_msg: defaultSysMsg, prompt: defaultPrompt, model: defaultModel });
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

    return (
        <Card className="space-y-5 p-6">
            <p className="text-sm text-ink-muted">Customize the LLM used for Word Breakdowns</p>

            <ProviderModelPicker
                provider={provider}
                modelName={modelName}
                providers={providers ?? []}
                onProviderChange={setProvider}
                onModelChange={setModelName}
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
                    <span className="relative inline-flex">
                        <button
                            type="button"
                            aria-label="Prompt Placeholders Help"
                            onClick={() => setHelpOpen((v) => !v)}
                            className="grid h-4 w-4 place-items-center rounded-full border border-ink/30 text-2xs leading-none text-ink-faint transition-colors hover:border-shu/60 hover:text-shu"
                        >
                            ?
                        </button>
                        <Popover
                            open={helpOpen}
                            onClose={() => setHelpOpen(false)}
                            className="w-80 p-3"
                        >
                            <p className="mb-1.5 font-medium text-ink">Placeholders</p>
                            <p className="mb-1 text-sm text-ink-muted">
                                <code className="rounded bg-ink/10 px-1 text-ink">
                                    {"{sentence}"}
                                </code>{" "}
                                &rarr; Sentence Being Analysed
                            </p>
                            <p className="text-sm text-ink-muted">
                                <code className="rounded bg-ink/10 px-1 text-ink">{"{focus}"}</code>{" "}
                                &rarr; Requested Word
                            </p>
                        </Popover>
                    </span>
                </div>
                <TextArea
                    id="prompt-text"
                    value={promptText}
                    onChange={(e) => setPromptText(e.target.value)}
                    className="font-mono text-[0.8rem]"
                />
            </div>

            <div className="flex flex-wrap gap-2">
                <Button onClick={onSave} loading={saving} disabled={deleting}>
                    {template ? "Update Template" : "Create Template"}
                </Button>
                <Button variant="secondary" onClick={onRevert} disabled={saving || deleting}>
                    Revert To Default
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
