/**
 * @packageDocumentation The slim player top bar: load media, subtitle style,
 * furigana toggle, and the SRT actions (generate / convert / LLM fix). The
 * long-running actions are submitted as jobs and tracked in the task tray, which
 * loads each result back into the player when it finishes.
 */

import {
    Sparkles,
    FileText,
    Clapperboard,
    RotateCcw,
    MoreHorizontal,
    Minus,
    Plus,
    Wand2,
} from "lucide-react";
import { useState } from "react";
import { toast } from "react-hot-toast";
import { apiGetTemplate } from "@/shared/llm/api";
import { ApiError, toastApiError } from "@/shared/api/errors";
import type { SubmitJobRequest } from "@/shared/jobs/types";
import { Button, IconButton, InfoTip, Popover, cn } from "@/shared/ui";
import { useIsMobile } from "@/shared/hooks/useMediaQuery";
import { usePlayer } from "@/contexts/PlayerContext";
import { useTasks } from "@/contexts/TaskContext";
import { useOperationSettings } from "@/contexts/OperationSettingsContext";
import { LoadMediaPopover } from "./LoadMediaPopover";
import { SubtitleStylePopover } from "./SubtitleStylePopover";

/**
 * The subtitle-context control: how many subtitle lines each side of a clicked
 * line are sent to a word breakdown as {context}. Persisted per profile, and
 * placed in the toolbar's breakdown popover (desktop) / the actions menu
 * (mobile) so it can be tuned while watching.
 *
 * @returns {JSX.Element} The control.
 */
function ContextControl() {
    const { settings, replace } = useOperationSettings();
    const n = settings.breakdownContextWindow;
    const set = (value: number) =>
        replace({ ...settings, breakdownContextWindow: Math.min(20, Math.max(0, value)) });
    const btn =
        "grid h-6 w-6 place-items-center rounded text-ink-muted transition-colors " +
        "hover:bg-ink/5 hover:text-ink disabled:pointer-events-none disabled:opacity-40";
    return (
        <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-1.5">
                <span className="text-sm font-medium text-ink">Subtitle Context</span>
                <InfoTip
                    content="How many nearby subtitle lines to send with a word lookup, so the model sees the surrounding scene."
                    wide
                />
            </div>
            <div className="flex items-center gap-0.5 rounded-control bg-surface-2 px-1 py-0.5">
                <button
                    type="button"
                    className={btn}
                    aria-label="Fewer context lines"
                    onClick={() => set(n - 1)}
                    disabled={n <= 0}
                >
                    <Minus size={14} />
                </button>
                <span className="w-5 text-center text-sm tabular-nums text-ink">{n}</span>
                <button
                    type="button"
                    className={btn}
                    aria-label="More context lines"
                    onClick={() => set(n + 1)}
                    disabled={n >= 20}
                >
                    <Plus size={14} />
                </button>
            </div>
        </div>
    );
}

/**
 * The PlayerToolbar component.
 *
 * @returns {JSX.Element} The toolbar.
 */
export function PlayerToolbar() {
    const {
        video,
        videoFileName,
        videoFileId,
        setVideoFileId,
        srt,
        srtFileId,
        setSrtFileId,
        showFurigana,
        setShowFurigana,
        clearPlayerState,
    } = usePlayer();
    const tasks = useTasks();
    const { whisperOpts, convertOpts } = useOperationSettings();

    // A profile file can be deleted from the Files tab while it's still loaded
    // here, leaving us driving an action off an id the server no longer has.
    // Submitting then 404s, so on that we drop the stale id (disabling its
    // buttons) and say why, rather than acting on a file that's gone.
    const submitByRef = async (req: SubmitJobRequest, onMissing: () => void): Promise<boolean> => {
        try {
            await tasks.submit(req);
            return true;
        } catch (err) {
            if (err instanceof ApiError && err.status === 404) {
                onMissing();
                toast.error("That File Was Deleted From Your Profile");
            } else {
                toastApiError(err);
            }
            return false;
        }
    };

    // Mobile -> Compact bar with the SRT actions tucked into a "More" menu
    // Desktop -> Keeps every control inline
    const isMobile = useIsMobile();
    const [moreOpen, setMoreOpen] = useState(false);
    const [llmOpen, setLlmOpen] = useState(false);

    // A profile video is operated on by reference (no re-upload); a device
    // video is uploaded first. Either way the tray tracks it and loads the
    // result back into the player.
    const handleGenerate = async () => {
        if (videoFileId) {
            const ok = await submitByRef(
                { type: "generate_srt", file_id: videoFileId, opts: whisperOpts() },
                () => setVideoFileId(null)
            );
            if (ok) toast.success("Subtitle Generation Started");
            return;
        }
        if (!video) return;
        void tasks.uploadAndSubmit(video, {
            jobType: "generate_srt",
            fileType: "video",
            opts: whisperOpts(),
        });
        toast.success("Subtitle Generation Started");
    };

    const handleConvert = async () => {
        if (!video && !videoFileId) return;
        const name = (videoFileName ?? video?.name ?? "").toLowerCase();
        if (name.endsWith(".mp4")) {
            toast.success("Already MP4");
            return;
        }
        if (videoFileId) {
            const ok = await submitByRef(
                { type: "convert", file_id: videoFileId, opts: convertOpts() },
                () => setVideoFileId(null)
            );
            if (ok) toast.success("Conversion Started");
            return;
        }
        if (!video) return;
        void tasks.uploadAndSubmit(video, {
            jobType: "convert",
            fileType: "video",
            opts: convertOpts(),
        });
        toast.success("Conversion Started");
    };

    const handleFixSrt = async () => {
        if (!srt) return;
        let template;
        try {
            template = await apiGetTemplate();
        } catch (err) {
            toastApiError(err);
            return;
        }
        if (!template) {
            toast.error("Configure An LLM Model In Your Profile To Fix Subtitles");
            return;
        }
        const model = template.srt_model || template.model;
        const sysMsg = template.srt_sys_msg || undefined;

        // A known profile SRT is fixed by reference. If that file was deleted
        // the submit 404s, so we drop the stale id and fall through to
        // re-uploading the in-memory SRT (a locally loaded one takes that path
        // directly, since its content lives here regardless).
        if (srtFileId) {
            try {
                await tasks.submit({ type: "fix_srt", file_id: srtFileId, model, sys_msg: sysMsg });
                toast.success("Subtitle Fix Started");
                return;
            } catch (err) {
                if (!(err instanceof ApiError && err.status === 404)) {
                    toastApiError(err);
                    return;
                }
                setSrtFileId(null);
            }
        }
        void tasks
            .uploadAndSubmit(srt, { jobType: "fix_srt", fileType: "srt", model, sysMsg })
            .catch(toastApiError);
        toast.success("Subtitle Fix Started");
    };

    const furiganaButton = (
        <button
            onClick={() => setShowFurigana(!showFurigana)}
            className={cn(
                "h-10 rounded-control px-3 text-sm font-medium transition-colors",
                showFurigana ? "bg-shu/15 text-shu" : "text-ink-muted hover:bg-ink/5 hover:text-ink"
            )}
            title="Toggle furigana"
            lang="ja"
        >
            ふり
        </button>
    );

    const resetButton = (
        <IconButton label="Reset player" onClick={clearPlayerState}>
            <RotateCcw size={18} />
        </IconButton>
    );

    // Shared once so that the desktop row and the mobile
    // "More" menu render the same buttons (full width inside the menu)
    const actionButtons = (
        <>
            <Button
                variant="secondary"
                size="sm"
                className={isMobile ? "w-full" : undefined}
                onClick={handleGenerate}
                disabled={!video && !videoFileId}
                title="Transcribe Audio Into Subtitles Using Whisper"
            >
                <FileText size={15} /> Generate SRT
            </Button>
            <Button
                variant="secondary"
                size="sm"
                className={isMobile ? "w-full" : undefined}
                onClick={handleConvert}
                disabled={!video && !videoFileId}
                title="Convert Video To MP4 Using FFMPEG"
            >
                <Clapperboard size={15} /> To MP4
            </Button>
            <Button
                variant="secondary"
                size="sm"
                className={isMobile ? "w-full" : undefined}
                onClick={handleFixSrt}
                disabled={!srt}
                title="Improve Subtitles With An LLM"
            >
                <Sparkles size={15} /> Fix SRT
            </Button>
        </>
    );

    // Per-side padding folds in the safe-area insets (0 on any non-notched
    // device, so identical to py-2 pl-16 pr-3 there). The left padding still
    // reserves room for the immersive floating menu button.
    const toolbarClasses =
        "relative z-30 flex items-center gap-1.5 border-b border-ink/10 bg-surface/80 pb-2 pl-[calc(4rem_+_var(--sal))] pr-[calc(0.75rem_+_var(--sar))] pt-[calc(0.5rem_+_var(--sat))] backdrop-blur";

    // Mobile
    // Compact Bar -> view controls + a "More" menu holding the SRT actions
    if (isMobile) {
        return (
            <div className={toolbarClasses}>
                <LoadMediaPopover />
                <SubtitleStylePopover />
                {furiganaButton}

                <div className="relative ml-auto">
                    <IconButton
                        label="More actions"
                        active={moreOpen}
                        onClick={() => setMoreOpen((v) => !v)}
                    >
                        <MoreHorizontal size={18} />
                    </IconButton>
                    <Popover
                        open={moreOpen}
                        onClose={() => setMoreOpen(false)}
                        align="right"
                        className="w-64 p-3"
                    >
                        <div className="flex flex-col gap-2">
                            <ContextControl />
                            <div className="h-px bg-ink/10" />
                            <div className="flex flex-col gap-1.5">{actionButtons}</div>
                        </div>
                    </Popover>
                </div>

                {resetButton}
            </div>
        );
    }

    // Desktop: every control inline, in the original order.
    return (
        <div className={toolbarClasses}>
            {furiganaButton}
            <span className="mx-1 h-6 w-px bg-ink/10" />

            <LoadMediaPopover />
            <SubtitleStylePopover />
            <span className="mx-1 h-6 w-px bg-ink/10" />

            {actionButtons}

            <div className="ml-auto flex items-center gap-1.5">
                <div className="relative">
                    <IconButton
                        label="Breakdown settings"
                        active={llmOpen}
                        onClick={() => setLlmOpen((v) => !v)}
                    >
                        <Wand2 size={18} />
                    </IconButton>
                    <Popover
                        open={llmOpen}
                        onClose={() => setLlmOpen(false)}
                        align="right"
                        className="w-64 p-4"
                    >
                        <h4 className="mb-2 text-2xs uppercase tracking-wide text-ink-faint">
                            Word Breakdown
                        </h4>
                        <ContextControl />
                    </Popover>
                </div>
                {resetButton}
            </div>
        </div>
    );
}
