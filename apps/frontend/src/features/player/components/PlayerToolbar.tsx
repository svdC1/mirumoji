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

    // Progress/status lives in the buttons (a non-null string = busy), so the
    // long-running actions don't need progress toasts — only success/error.
    const [genStatus, setGenStatus] = useState<string | null>(null);
    const [convStatus, setConvStatus] = useState<string | null>(null);
    const [fixStatus, setFixStatus] = useState<string | null>(null);
    const generating = genStatus !== null;
    const converting = convStatus !== null;
    const fixing = fixStatus !== null;
    const busy = generating || converting || fixing;

    const handleGenerate = async () => {
        if (!video) return;
        setGenStatus("Uploading 0%");
        try {
            const result = await generateSrt(
                video,
                (p) => setGenStatus(`Uploading ${p.toFixed(0)}%`),
                () => setGenStatus("Generating …")
            );
            const file = new File([result.srt_content], `${video.name}.srt`, {
                type: "application/x-subrip",
            });
            setSrt(file);
            setSrtFileName(file.name);
            setSrtFileId(result.file_id); // generated SRT is persisted server-side
            toast.success("Subtitles Generated");
        } catch (err) {
            toastApiError(err);
        } finally {
            setGenStatus(null);
        }
    };

    const handleConvert = async () => {
        if (!video) return;
        if (video.name.toLowerCase().endsWith(".mp4")) {
            toast.success("Already MP4");
            return;
        }
        setConvStatus("Uploading 0%");
        try {
            const result = await convertToMp4(
                video,
                (p) => setConvStatus(`Uploading ${p.toFixed(0)}%`),
                () => setConvStatus("Converting …")
            );
            setVideo(null);
            setVideoUrl(staticUrl(result.converted_video_url));
            setVideoFileName(result.converted_video_url);
            toast.success("Conversion Complete");
        } catch (err) {
            toastApiError(err);
        } finally {
            setConvStatus(null);
        }
    };

    const handleFixSrt = async () => {
        if (!srt) return;
        setFixStatus("Fixing …");
        try {
            const template = await apiGetTemplate();
            if (!template) {
                toast.error("Configure An LLM Model In Your Profile To Fix Subtitles");
                return;
            }
            const text = await srt.text();
            const { srt: fixed } = await apiFixSrt({
                srt: text,
                model: template.srt_model || template.model,
                sys_msg: template.srt_sys_msg || undefined,
            });

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
            toast.success("Subtitles Fixed");
        } catch (err) {
            toastApiError(err);
        } finally {
            setFixStatus(null);
        }
    };

    return (
        <div className="relative z-30 flex items-center gap-1.5 border-b border-ink/10 bg-surface/80 py-2 pl-16 pr-3 backdrop-blur">
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

            <LoadMediaPopover />
            <SubtitleStylePopover />
            <span className="mx-1 h-6 w-px bg-ink/10" />

            <Button
                variant="secondary"
                size="sm"
                onClick={handleGenerate}
                loading={generating}
                disabled={!video || busy}
                title="Transcribe Audio Into Subtitles Using Whisper"
            >
                {generating ? (
                    <span className="tabular-nums">{genStatus}</span>
                ) : (
                    <>
                        <FileText size={15} /> Generate SRT
                    </>
                )}
            </Button>
            <Button
                variant="secondary"
                size="sm"
                onClick={handleConvert}
                loading={converting}
                disabled={!video || busy}
                title="Convert Video To MP4 Using FFMPEG"
            >
                {converting ? (
                    <span className="tabular-nums">{convStatus}</span>
                ) : (
                    <>
                        <Clapperboard size={15} /> To MP4
                    </>
                )}
            </Button>
            <Button
                variant="secondary"
                size="sm"
                onClick={handleFixSrt}
                loading={fixing}
                disabled={!srt || busy}
                title="Improve Subtitles With An LLM"
            >
                {fixing ? (
                    fixStatus
                ) : (
                    <>
                        <Sparkles size={15} /> Fix SRT
                    </>
                )}
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
