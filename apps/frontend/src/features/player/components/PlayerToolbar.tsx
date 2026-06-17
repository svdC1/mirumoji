/**
 * @packageDocumentation The slim player top bar: load media, subtitle style,
 * furigana toggle, and the SRT actions (generate / convert / LLM fix). The
 * long-running actions are submitted as jobs and tracked in the task tray, which
 * loads each result back into the player when it finishes.
 */

import { Sparkles, FileText, Clapperboard, RotateCcw, MoreHorizontal } from "lucide-react";
import { useState } from "react";
import { toast } from "react-hot-toast";
import { apiGetTemplate } from "@/shared/llm/api";
import { toastApiError } from "@/shared/api/errors";
import { Button, IconButton, Popover, cn } from "@/shared/ui";
import { useIsMobile } from "@/shared/hooks/useMediaQuery";
import { usePlayer } from "@/contexts/PlayerContext";
import { useTasks } from "@/contexts/TaskContext";
import { LoadMediaPopover } from "./LoadMediaPopover";
import { SubtitleStylePopover } from "./SubtitleStylePopover";

/**
 * The PlayerToolbar component.
 *
 * @returns {JSX.Element} The toolbar.
 */
export function PlayerToolbar() {
    const { video, videoUrl, srt, srtFileId, showFurigana, setShowFurigana, clearPlayerState } =
        usePlayer();
    const tasks = useTasks();

    // Mobile -> Compact bar with the SRT actions tucked into a "More" menu
    // Desktop -> Keeps every control inline
    const isMobile = useIsMobile();
    const [moreOpen, setMoreOpen] = useState(false);

    const handleGenerate = () => {
        if (!video) return;
        void tasks.uploadAndSubmit(video, { jobType: "generate_srt", fileType: "video" });
        toast.success("Subtitle Generation Started");
    };

    const handleConvert = () => {
        if (!video) return;
        if (video.name.toLowerCase().endsWith(".mp4")) {
            toast.success("Already MP4");
            return;
        }
        void tasks.uploadAndSubmit(video, { jobType: "convert", fileType: "video" });
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
        // A known profile SRT is fixed by reference; a locally loaded one is
        // uploaded first. Either way the tray tracks it and loads the result.
        const promise = srtFileId
            ? tasks.submit({ type: "fix_srt", file_id: srtFileId, model, sys_msg: sysMsg })
            : tasks.uploadAndSubmit(srt, { jobType: "fix_srt", fileType: "srt", model, sysMsg });
        void promise.catch(toastApiError);
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
                disabled={!video}
                title="Transcribe Audio Into Subtitles Using Whisper"
            >
                <FileText size={15} /> Generate SRT
            </Button>
            <Button
                variant="secondary"
                size="sm"
                className={isMobile ? "w-full" : undefined}
                onClick={handleConvert}
                disabled={!video || !!videoUrl}
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

    const toolbarClasses =
        "relative z-30 flex items-center gap-1.5 border-b border-ink/10 bg-surface/80 py-2 pl-16 pr-3 backdrop-blur";

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
                        className="w-56 p-2"
                    >
                        <div className="flex flex-col gap-1.5">{actionButtons}</div>
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

            <div className="ml-auto flex items-center gap-1.5">{resetButton}</div>
        </div>
    );
}
