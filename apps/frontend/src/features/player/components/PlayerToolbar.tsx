/**
 * @packageDocumentation The slim player top bar: load media, subtitle style,
 * furigana toggle, and the SRT actions (generate / convert / LLM fix).
 */

import { useState } from "react";
import { PanelRightOpen, Sparkles, FileText, Clapperboard, RotateCcw } from "lucide-react";
import { toast } from "react-hot-toast";
import { apiGetTemplate, apiFixSrt } from "@/shared/llm/api";
import { toastApiError } from "@/shared/api/errors";
import { staticUrl } from "@/shared/format/files";
import { Button, IconButton, cn } from "@/shared/ui";
import { usePlayer } from "@/contexts/PlayerContext";
import { useProfile } from "@/contexts/ProfileContext";
import { LoadMediaPopover } from "./LoadMediaPopover";
import { SubtitleStylePopover } from "./SubtitleStylePopover";
import { generateSrt, convertToMp4, saveSubtitles } from "../api";

export interface PlayerToolbarProps {
    panelCollapsed: boolean;
    onTogglePanel: () => void;
}

/**
 * The PlayerToolbar component.
 *
 * @param {PlayerToolbarProps} props The props.
 * @returns {JSX.Element} The toolbar.
 */
export function PlayerToolbar({ panelCollapsed, onTogglePanel }: PlayerToolbarProps) {
    const {
        video,
        srt,
        srtFileId,
        setSrt,
        setSrtFileName,
        setSrtFileId,
        setVideo,
        setVideoUrl,
        setVideoFileName,
        showFurigana,
        setShowFurigana,
        clearPlayerState,
    } = usePlayer();
    const { profileId } = useProfile();

    const [generating, setGenerating] = useState(false);
    const [converting, setConverting] = useState(false);
    const [fixing, setFixing] = useState(false);
    const busy = generating || converting || fixing;

    const handleGenerate = async () => {
        if (!video) return;
        setGenerating(true);
        const tId = toast.loading("Uploading…");
        try {
            const result = await generateSrt(
                video,
                (p) => toast.loading(`Uploading… ${p.toFixed(0)}%`, { id: tId }),
                () => toast.loading("Generating…", { id: tId })
            );
            const file = new File([result.srt_content], `${video.name}.srt`, {
                type: "application/x-subrip",
            });
            setSrt(file);
            setSrtFileName(file.name);
            setSrtFileId(result.file_id); // generated SRT is persisted server-side
            toast.success("Subtitles Generated", { id: tId });
        } catch (err) {
            toastApiError(err, tId);
        } finally {
            setGenerating(false);
        }
    };

    const handleConvert = async () => {
        if (!video) return;
        if (video.name.toLowerCase().endsWith(".mp4")) {
            toast.success("Already MP4");
            return;
        }
        setConverting(true);
        const tId = toast.loading("Uploading…");
        try {
            const result = await convertToMp4(
                video,
                (p) => toast.loading(`Uploading… ${p.toFixed(0)}%`, { id: tId }),
                () => toast.loading("Converting…", { id: tId })
            );
            setVideo(null);
            setVideoUrl(staticUrl(result.converted_video_url));
            setVideoFileName(result.converted_video_url);
            toast.success("Conversion Complete", { id: tId });
        } catch (err) {
            toastApiError(err, tId);
        } finally {
            setConverting(false);
        }
    };

    const handleFixSrt = async () => {
        if (!srt) return;
        setFixing(true);
        const tId = toast.loading("Checking model…");
        try {
            const template = await apiGetTemplate();
            if (!template) {
                toast.error("Configure An LLM Model In Your Profile To Fix Subtitles", { id: tId });
                return;
            }
            toast.loading("Fixing subtitles…", { id: tId });
            const text = await srt.text();
            const { srt: fixed } = await apiFixSrt({ srt: text, model: template.model });

            // Persist the fixed SRT to the profile (replacing the source file in
            // place when it's a known profile file), then re-tokenize locally.
            if (profileId) {
                try {
                    const saved = await saveSubtitles({
                        content: fixed,
                        file_id: srtFileId ?? undefined,
                        name: srt.name,
                    });
                    setSrtFileId(saved.id);
                } catch (err) {
                    console.error("Failed to persist fixed SRT:", err);
                }
            }

            const file = new File([fixed], srt.name, { type: "application/x-subrip" });
            setSrt(file);
            setSrtFileName(file.name);
            toast.success("Subtitles Fixed", { id: tId });
        } catch (err) {
            toastApiError(err, tId);
        } finally {
            setFixing(false);
        }
    };

    return (
        <div className="relative z-30 flex items-center gap-1.5 border-b border-ink/10 bg-surface/80 py-2 pl-16 pr-3 backdrop-blur">
            <LoadMediaPopover />
            <SubtitleStylePopover />
            <button
                onClick={() => setShowFurigana(!showFurigana)}
                className={cn(
                    "h-10 rounded-control px-3 text-sm font-medium transition-colors",
                    showFurigana
                        ? "bg-shu/15 text-shu"
                        : "text-ink-muted hover:bg-ink/5 hover:text-ink"
                )}
                title="Toggle furigana"
                lang="ja"
            >
                ふり
            </button>

            <span className="mx-1 h-6 w-px bg-ink/10" />

            <Button
                variant="secondary"
                size="sm"
                onClick={handleGenerate}
                loading={generating}
                disabled={!video || busy}
            >
                <FileText size={15} /> Generate SRT
            </Button>
            <Button
                variant="secondary"
                size="sm"
                onClick={handleConvert}
                loading={converting}
                disabled={!video || busy}
            >
                <Clapperboard size={15} /> To MP4
            </Button>
            <Button
                variant="secondary"
                size="sm"
                onClick={handleFixSrt}
                loading={fixing}
                disabled={!srt || busy}
                title="Clean up the subtitles with an LLM"
            >
                <Sparkles size={15} /> Fix SRT
            </Button>

            <div className="ml-auto flex items-center gap-1.5">
                <IconButton label="Reset player" onClick={clearPlayerState} disabled={busy}>
                    <RotateCcw size={18} />
                </IconButton>
                {panelCollapsed && (
                    <IconButton label="Show subtitles" onClick={onTogglePanel}>
                        <PanelRightOpen size={18} />
                    </IconButton>
                )}
            </div>
        </div>
    );
}
