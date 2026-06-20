/**
 * @packageDocumentation The batch operation dialog: pick one operation to run
 * across the selected files. The options themselves come from the Advanced
 * settings (Whisper / conversion) or the LLM Template (subtitle fix), so this is
 * just a picker. Submitting drops a batch job into the Tasks tray.
 */

import { useEffect, useState } from "react";
import { Clapperboard, FileText, Mic, Sparkles } from "lucide-react";
import { toast } from "react-hot-toast";
import { useTasks } from "@/contexts/TaskContext";
import { useOperationSettings } from "@/contexts/OperationSettingsContext";
import { apiGetTemplate } from "@/shared/llm/api";
import { toastApiError } from "@/shared/api/errors";
import { inferFileType } from "@/shared/format/files";
import { Button, Dialog, cn } from "@/shared/ui";
import type { BatchJobType, BatchSubmitRequest } from "@/shared/jobs/types";
import type { ProfileFile } from "../types";

const OPERATIONS: {
    type: BatchJobType;
    label: string;
    description: string;
    icon: typeof FileText;
}[] = [
    {
        type: "batch_generate_srt",
        label: "Generate Subtitles",
        description: "Transcribe each video or audio file into a subtitle file",
        icon: FileText,
    },
    {
        type: "batch_transcribe",
        label: "Transcribe",
        description: "Transcribe each audio file into a text transcript",
        icon: Mic,
    },
    {
        type: "batch_convert",
        label: "Convert To MP4",
        description: "Re-encode each video to MP4",
        icon: Clapperboard,
    },
    {
        type: "batch_fix_srt",
        label: "Fix Subtitles",
        description: "Clean each subtitle file with your LLM Template model",
        icon: Sparkles,
    },
];

// What each operation needs every selected file to be. inferFileType (extension)
// is the only reliable media-vs-non-media signal — the browser can't tell an
// undecodable video from a non-media file — so a text file can't be fed to
// FFmpeg/Whisper, nor a video to the subtitle fixer.
const OP_ACCEPTS: Record<BatchJobType, { types: string[]; note: string }> = {
    batch_generate_srt: { types: ["video", "audio"], note: "Media Files Only" },
    batch_transcribe: { types: ["audio"], note: "Audio Files Only" },
    batch_convert: { types: ["video"], note: "Video Files Only" },
    batch_fix_srt: { types: ["srt"], note: "Subtitle Files Only" },
};

/**
 * The BatchDialog component.
 *
 * @param {object} props The props.
 * @param {boolean} props.open Whether the dialog is open.
 * @param {ProfileFile[]} props.files The selected profile files.
 * @param {() => void} props.onClose Closes the dialog.
 * @param {() => void} [props.onSubmitted] Called after a batch is submitted.
 * @returns {JSX.Element} The dialog.
 */
export function BatchDialog({
    open,
    files,
    onClose,
    onSubmitted,
}: {
    open: boolean;
    files: ProfileFile[];
    onClose: () => void;
    onSubmitted?: () => void;
}) {
    const { submitBatch } = useTasks();
    const { whisperOpts, convertOpts, settings } = useOperationSettings();
    const [type, setType] = useState<BatchJobType>("batch_generate_srt");
    const [submitting, setSubmitting] = useState(false);

    const fileIds = files.map((f) => f.id);

    // An operation can run only if every selected file is a kind it accepts, so
    // a non-matching file (a text file under Convert, a video under Fix
    // Subtitles) is never fed to the wrong tool.
    const isOpDisabled = (t: BatchJobType) =>
        files.length === 0 ||
        !files.every((f) => OP_ACCEPTS[t].types.includes(inferFileType(f.name) ?? ""));

    // A stable signature of the selection's file kinds, so the reset effect only
    // re-runs when the selection actually changes (not on every render).
    const selectionSig = files.map((f) => inferFileType(f.name) ?? "?").join("|");

    // Drop an operation the current selection no longer supports, settling on
    // the first one it does.
    useEffect(() => {
        if (!open || !isOpDisabled(type)) return;
        const fallback = OPERATIONS.find((op) => !isOpDisabled(op.type));
        if (fallback) setType(fallback.type);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [open, type, selectionSig]);

    const buildRequest = async (): Promise<BatchSubmitRequest | null> => {
        if (isOpDisabled(type)) {
            toast.error("That Operation Doesn't Match The Selected Files");
            return null;
        }
        const base = { type, file_ids: fileIds };
        if (type === "batch_generate_srt") return { ...base, opts: whisperOpts() };
        if (type === "batch_transcribe") {
            return { ...base, opts: { ...whisperOpts(), clean_audio: settings.cleanAudio } };
        }
        if (type === "batch_convert") return { ...base, opts: convertOpts() };
        // batch_fix_srt: model + system message come from the LLM Template,
        // exactly like the single-file Fix SRT action.
        const template = await apiGetTemplate();
        if (!template) {
            toast.error("Configure An LLM Model In Your Profile To Fix Subtitles");
            return null;
        }
        return {
            ...base,
            model: template.srt_model || template.model,
            sys_msg: template.srt_sys_msg || undefined,
        };
    };

    const run = async () => {
        setSubmitting(true);
        try {
            const req = await buildRequest();
            if (!req) return;
            await submitBatch(req);
            toast.success(`Batch Started · ${fileIds.length} File(s)`);
            onSubmitted?.();
            onClose();
        } catch (err) {
            toastApiError(err);
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <Dialog open={open} onClose={onClose} className="max-w-md">
            <div className="space-y-4 p-5">
                <header>
                    <h2 className="font-display text-lg text-ink">Run Batch</h2>
                    <p className="text-sm text-ink-muted">
                        One Operation Across {fileIds.length} Selected File(s)
                    </p>
                </header>

                <ul className="space-y-2">
                    {OPERATIONS.map((op) => {
                        const Icon = op.icon;
                        const disabled = isOpDisabled(op.type);
                        const active = op.type === type && !disabled;
                        return (
                            <li key={op.type}>
                                <button
                                    type="button"
                                    disabled={disabled}
                                    onClick={() => setType(op.type)}
                                    className={cn(
                                        "flex w-full items-start gap-3 rounded-card border px-3 py-2.5 text-left transition-colors",
                                        disabled
                                            ? "cursor-not-allowed border-ink/10 opacity-40"
                                            : active
                                              ? "border-shu/40 bg-shu/10"
                                              : "border-ink/10 hover:bg-ink/5"
                                    )}
                                >
                                    <Icon
                                        size={18}
                                        className={cn(
                                            "mt-0.5 shrink-0",
                                            active ? "text-shu" : "text-ink-faint"
                                        )}
                                    />
                                    <span className="min-w-0">
                                        <span className="block text-sm font-medium text-ink">
                                            {op.label}
                                        </span>
                                        <span className="block text-2xs text-ink-muted">
                                            {disabled ? OP_ACCEPTS[op.type].note : op.description}
                                        </span>
                                    </span>
                                </button>
                            </li>
                        );
                    })}
                </ul>

                <div className="flex justify-end gap-2 pt-1">
                    <Button variant="ghost" onClick={onClose} disabled={submitting}>
                        Cancel
                    </Button>
                    <Button
                        onClick={run}
                        loading={submitting}
                        disabled={fileIds.length === 0 || isOpDisabled(type)}
                    >
                        Run Batch
                    </Button>
                </div>
            </div>
        </Dialog>
    );
}
